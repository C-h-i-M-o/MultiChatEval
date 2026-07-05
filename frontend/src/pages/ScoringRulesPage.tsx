import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Form, Input, InputNumber, Modal, Popconfirm, Select, Space, Switch, Tabs, Tag, message } from "antd";
import type { TableColumnsType } from "antd";

import {
  ApiError,
  createRuleTerm,
  deleteRuleTerm,
  listJudgePromptGroups,
  listJudgePromptTemplates,
  listRuleDictionaries,
  listRuleTerms,
  updateJudgePromptTemplate,
  updateRuleTerm,
  updateRuleTermStatus,
  validateJudgePromptGroup
} from "../api/client";
import type { JudgePromptGroup, JudgePromptTemplate, RuleDictionary, RuleTerm, RuleTermPayload } from "../api/client";
import { AdminDataTable } from "../components/admin/AdminDataTable";
import { AdminFilterBar } from "../components/admin/AdminFilterBar";

const DEFAULT_PAGE_SIZE = 10;
type EnabledFilter = "all" | "true" | "false";

export function ScoringRulesPage() {
  const [dictionaries, setDictionaries] = useState<RuleDictionary[]>([]);
  const [terms, setTerms] = useState<RuleTerm[]>([]);
  const [groups, setGroups] = useState<JudgePromptGroup[]>([]);
  const [templates, setTemplates] = useState<JudgePromptTemplate[]>([]);
  const [keyword, setKeyword] = useState("");
  const [dictionaryType, setDictionaryType] = useState("all");
  const [enabledFilter, setEnabledFilter] = useState<EnabledFilter>("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [termModalOpen, setTermModalOpen] = useState(false);
  const [editingTerm, setEditingTerm] = useState<RuleTerm | null>(null);
  const [templateModalOpen, setTemplateModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<JudgePromptTemplate | null>(null);
  const [termForm] = Form.useForm<RuleTermPayload>();
  const [templateForm] = Form.useForm<{ content: string; outputSchemaText: string; enabled: boolean }>();

  const enabledValue = enabledFilter === "all" ? null : enabledFilter === "true";

  const loadTerms = useCallback(async () => {
    setLoading(true);
    try {
      const [dictionaryItems, termResult] = await Promise.all([
        listRuleDictionaries(),
        listRuleTerms({ page, pageSize, keyword, dictionaryType, enabled: enabledValue })
      ]);
      setDictionaries(dictionaryItems);
      setTerms(termResult.items);
      setTotal(termResult.total);
    } catch (error) {
      message.error(getErrorMessage(error, "规则词表加载失败"));
    } finally {
      setLoading(false);
    }
  }, [dictionaryType, enabledValue, keyword, page, pageSize]);

  const loadPrompts = useCallback(async () => {
    try {
      const [groupItems, templateItems] = await Promise.all([listJudgePromptGroups(), listJudgePromptTemplates()]);
      setGroups(groupItems);
      setTemplates(templateItems);
    } catch (error) {
      message.error(getErrorMessage(error, "Judge Prompt 加载失败"));
    }
  }, []);

  useEffect(() => {
    void loadTerms();
    void loadPrompts();
  }, [loadTerms, loadPrompts]);

  const termColumns = useMemo<TableColumnsType<RuleTerm>>(
    () => [
      { title: "词典类型", dataIndex: "dictionaryType", width: 150 },
      { title: "分类", dataIndex: "category", width: 120 },
      { title: "词条内容", dataIndex: "content" },
      { title: "匹配", dataIndex: "matchType", width: 100, render: (value: RuleTerm["matchType"]) => (value === "regex" ? "正则" : "关键词") },
      { title: "严重级别", dataIndex: "severity", width: 100 },
      { title: "状态", dataIndex: "enabled", width: 90, render: (enabled: boolean) => <Tag color={enabled ? "success" : "default"}>{enabled ? "启用" : "禁用"}</Tag> },
      {
        title: "操作",
        width: 210,
        render: (_, term) => (
          <Space>
            <Button size="small" onClick={() => openTermModal(term)}>编辑</Button>
            <Button size="small" onClick={() => void toggleTerm(term)}>{term.enabled ? "禁用" : "启用"}</Button>
            <Popconfirm title="删除词条" description="确认删除该词条？" onConfirm={() => void removeTerm(term.id)}>
              <Button size="small" danger>删除</Button>
            </Popconfirm>
          </Space>
        )
      }
    ],
    []
  );

  const templateColumns = useMemo<TableColumnsType<JudgePromptTemplate>>(
    () => [
      { title: "Group", dataIndex: "groupCode", width: 140 },
      { title: "模板", dataIndex: "code", width: 160 },
      { title: "正文", dataIndex: "content", ellipsis: true },
      { title: "状态", dataIndex: "enabled", width: 90, render: (enabled: boolean) => <Tag color={enabled ? "success" : "default"}>{enabled ? "启用" : "禁用"}</Tag> },
      { title: "操作", width: 120, render: (_, template) => <Button size="small" onClick={() => openTemplateModal(template)}>编辑</Button> }
    ],
    []
  );

  function resetToFirstPage(): void {
    setPage(1);
  }

  function openTermModal(term: RuleTerm | null): void {
    setEditingTerm(term);
    termForm.setFieldsValue(
      term
        ? { dictionaryId: term.dictionaryId, category: term.category, content: term.content, matchType: term.matchType, severity: term.severity, enabled: term.enabled }
        : { dictionaryId: dictionaries[0]?.id || 0, category: "general", content: "", matchType: "keyword", severity: 1, enabled: true }
    );
    setTermModalOpen(true);
  }

  async function submitTerm(): Promise<void> {
    try {
      const payload = await termForm.validateFields();
      if (editingTerm) {
        await updateRuleTerm(editingTerm.id, payload);
      } else {
        await createRuleTerm(payload);
      }
      message.success("词表已保存，后端缓存将在下次评分时刷新");
      setTermModalOpen(false);
      await loadTerms();
    } catch (error) {
      message.error(getErrorMessage(error, "词条保存失败"));
    }
  }

  async function toggleTerm(term: RuleTerm): Promise<void> {
    try {
      await updateRuleTermStatus(term.id, !term.enabled);
      message.success("词条状态已更新，后端缓存将在下次评分时刷新");
      await loadTerms();
    } catch (error) {
      message.error(getErrorMessage(error, "词条状态更新失败"));
    }
  }

  async function removeTerm(id: number): Promise<void> {
    try {
      await deleteRuleTerm(id);
      message.success("词条已删除，后端缓存将在下次评分时刷新");
      await loadTerms();
    } catch (error) {
      message.error(getErrorMessage(error, "词条删除失败"));
    }
  }

  function openTemplateModal(template: JudgePromptTemplate): void {
    setEditingTemplate(template);
    templateForm.setFieldsValue({
      content: template.content,
      outputSchemaText: JSON.stringify(template.outputSchema, null, 2),
      enabled: template.enabled
    });
    setTemplateModalOpen(true);
  }

  async function submitTemplate(): Promise<void> {
    if (!editingTemplate) {
      return;
    }
    try {
      const values = await templateForm.validateFields();
      await updateJudgePromptTemplate(editingTemplate.id, {
        content: values.content,
        outputSchema: JSON.parse(values.outputSchemaText) as Record<string, object>,
        enabled: values.enabled
      });
      message.success("Prompt 模板已保存，后端缓存将在下次评分时刷新");
      setTemplateModalOpen(false);
      await loadPrompts();
    } catch (error) {
      message.error(getErrorMessage(error, "Prompt 模板保存失败"));
    }
  }

  async function validateGroup(group: JudgePromptGroup): Promise<void> {
    try {
      const result = await validateJudgePromptGroup(group.id);
      message[result.valid ? "success" : "warning"](result.valid ? `${group.code} 可用于评分` : result.issues.join("；"));
    } catch (error) {
      message.error(getErrorMessage(error, "Prompt Group 校验失败"));
    }
  }

  return (
    <section className="admin-page scoring-page">
      <header className="page-head"><div><p className="eyebrow">Scoring Config</p><h2>评分配置</h2></div></header>
      <Tabs
        items={[
          {
            key: "terms",
            label: "规则词表",
            children: (
              <div className="admin-tab-panel-stack">
                <AdminFilterBar
                  title="词表筛选"
                  total={total}
                  searchValue={keyword}
                  searchPlaceholder="搜索词条"
                  roleValue={dictionaryType}
                  roleOptions={[{ value: "all", label: "全部词典" }, ...dictionaries.map((item) => ({ value: item.dictionaryType, label: item.name }))]}
                  statusValue={enabledFilter}
                  statusOptions={[{ value: "all", label: "全部状态" }, { value: "true", label: "启用" }, { value: "false", label: "禁用" }]}
                  loading={loading}
                  onSearchChange={(value) => { setKeyword(value); resetToFirstPage(); }}
                  onSearchSubmit={resetToFirstPage}
                  onRoleChange={(value) => { setDictionaryType(value); resetToFirstPage(); }}
                  onStatusChange={(value) => { setEnabledFilter(value); resetToFirstPage(); }}
                  onRefresh={() => void loadTerms()}
                  actions={<Button type="primary" onClick={() => openTermModal(null)}>新增词条</Button>}
                />
                <AdminDataTable rowKey="id" columns={termColumns} dataSource={terms} loading={loading} page={page} pageSize={pageSize} total={total} totalLabel="条词条" onPageChange={(nextPage, nextPageSize) => { setPage(nextPage); setPageSize(nextPageSize); }} />
              </div>
            )
          },
          {
            key: "prompts",
            label: "Judge Prompt",
            children: (
              <div className="admin-tab-panel-stack">
                <div className="admin-toolbar">
                  {groups.map((group) => <Button key={group.id} onClick={() => void validateGroup(group)}>校验 {group.code}</Button>)}
                  <Button onClick={() => void loadPrompts()}>刷新</Button>
                </div>
                <AdminDataTable rowKey="id" columns={templateColumns} dataSource={templates} loading={false} page={1} pageSize={templates.length || 10} total={templates.length} totalLabel="个模板" onPageChange={() => undefined} />
              </div>
            )
          }
        ]}
      />
      <Modal title={editingTerm ? "编辑词条" : "新增词条"} open={termModalOpen} onOk={() => void submitTerm()} onCancel={() => setTermModalOpen(false)} okText="保存" cancelText="取消">
        <Form form={termForm} layout="vertical">
          <Form.Item name="dictionaryId" label="词典" rules={[{ required: true }]}><Select options={dictionaries.map((item) => ({ value: item.id, label: item.name }))} /></Form.Item>
          <Form.Item name="category" label="分类" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="content" label="词条内容" rules={[{ required: true }]}><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="matchType" label="匹配方式" rules={[{ required: true }]}><Select options={[{ value: "keyword", label: "关键词" }, { value: "regex", label: "正则" }]} /></Form.Item>
          <Form.Item name="severity" label="严重级别" rules={[{ required: true }]}><InputNumber min={1} max={10} /></Form.Item>
          <Form.Item name="enabled" label="启用" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>
      <Modal title={`编辑模板 ${editingTemplate?.code || ""}`} open={templateModalOpen} onOk={() => void submitTemplate()} onCancel={() => setTemplateModalOpen(false)} okText="保存" cancelText="取消" width="min(860px, 94vw)">
        <Form form={templateForm} layout="vertical">
          <Form.Item name="content" label="模板正文" rules={[{ required: true }]}><Input.TextArea rows={10} /></Form.Item>
          <Form.Item name="outputSchemaText" label="output_schema" rules={[{ required: true }]}><Input.TextArea rows={8} /></Form.Item>
          <Form.Item name="enabled" label="启用" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>
    </section>
  );
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}
