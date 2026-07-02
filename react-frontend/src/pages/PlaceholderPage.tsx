interface PlaceholderPageProps {
  title: string;
  description: string;
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <section className="placeholder-page">
      <p className="eyebrow">React 阶段二</p>
      <h2>{title}</h2>
      <p>{description}</p>
    </section>
  );
}
