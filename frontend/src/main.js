import { createApp } from "vue";
import ElementPlus from "element-plus";
import zhCn from "element-plus/es/locale/lang/zh-cn";
import "element-plus/dist/index.css";

import App from "./App.vue";
import { router } from "./router";
import { pinia } from "./stores";
import "./styles/main.css";

const elementPlusLocale = {
  ...zhCn,
  el: {
    ...zhCn.el,
    pagination: {
      ...zhCn.el.pagination,
      pagesize: "/页"
    }
  }
};

createApp(App).use(pinia).use(router).use(ElementPlus, { locale: elementPlusLocale }).mount("#app");
