import React from "react";

/**
 * Minimal, dependency-free markdown renderer for level content:
 * headings, lists, bold, inline code and fenced code blocks.
 * (Content is authored in-house — no untrusted HTML, no dangerouslySetInnerHTML.)
 */
export default function Markdown({ text }: { text: string }) {
  const lines = text.split("\n");
  const blocks: React.ReactNode[] = [];
  let list: React.ReactNode[] = [];
  let code: string[] | null = null;

  const inline = (s: string, keyPrefix: string): React.ReactNode => {
    const parts: React.ReactNode[] = [];
    const regex = /(\*\*[^*]+\*\*|`[^`]+`)/g;
    let last = 0;
    let m: RegExpExecArray | null;
    let i = 0;
    while ((m = regex.exec(s)) !== null) {
      if (m.index > last) parts.push(s.slice(last, m.index));
      const token = m[0];
      if (token.startsWith("**")) {
        parts.push(
          <strong key={`${keyPrefix}-b${i}`} className="font-semibold text-fg">
            {token.slice(2, -2)}
          </strong>
        );
      } else {
        parts.push(
          <code
            key={`${keyPrefix}-c${i}`}
            className="rounded-md border border-border bg-surface-2 px-1.5 py-0.5 font-mono text-[12.5px] text-accent"
          >
            {token.slice(1, -1)}
          </code>
        );
      }
      last = m.index + token.length;
      i += 1;
    }
    if (last < s.length) parts.push(s.slice(last));
    return parts;
  };

  const flushList = () => {
    if (list.length) {
      blocks.push(
        <ul key={`ul-${blocks.length}`} className="my-2 space-y-1.5 pl-1">
          {list.map((item, i) => (
            <li key={i} className="flex gap-2.5 text-sm leading-relaxed text-muted">
              <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-primary/70" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      );
      list = [];
    }
  };

  lines.forEach((raw, idx) => {
    const line = raw.trimEnd();

    if (line.startsWith("```")) {
      if (code === null) {
        flushList();
        code = [];
      } else {
        blocks.push(
          <pre
            key={`pre-${idx}`}
            className="my-3 overflow-x-auto rounded-xl border border-border bg-[#0A0F1E] p-3.5 font-mono text-[12.5px] leading-relaxed text-accent"
          >
            {code.join("\n")}
          </pre>
        );
        code = null;
      }
      return;
    }
    if (code !== null) {
      code.push(line);
      return;
    }

    if (/^[-*]\s+/.test(line)) {
      list.push(<>{inline(line.replace(/^[-*]\s+/, ""), `l${idx}`)}</>);
      return;
    }
    if (/^\d+\.\s+/.test(line)) {
      const num = line.match(/^(\d+)\./)?.[1];
      list.push(
        <span className="flex gap-2.5">
          <span className="font-mono text-[12px] font-bold text-primary">{num}.</span>
          <span>{inline(line.replace(/^\d+\.\s+/, ""), `l${idx}`)}</span>
        </span>
      );
      return;
    }

    flushList();

    if (line.startsWith("### ")) {
      blocks.push(
        <h4 key={idx} className="mb-1 mt-4 text-[13px] font-bold uppercase tracking-wide text-primary">
          {line.slice(4)}
        </h4>
      );
    } else if (line.startsWith("## ")) {
      blocks.push(
        <h3 key={idx} className="mb-1.5 mt-5 text-[15px] font-bold text-fg">
          {line.slice(3)}
        </h3>
      );
    } else if (line.startsWith("# ")) {
      blocks.push(
        <h3 key={idx} className="mb-2 mt-3 text-base font-extrabold text-fg">
          {inline(line.slice(2), `h${idx}`)}
        </h3>
      );
    } else if (line.trim() === "") {
      blocks.push(<div key={idx} className="h-2" />);
    } else {
      blocks.push(
        <p key={idx} className="my-1.5 text-sm leading-relaxed text-muted">
          {inline(line, `p${idx}`)}
        </p>
      );
    }
  });
  flushList();
  if (code !== null) {
    blocks.push(
      <pre key="pre-last" className="my-3 overflow-x-auto rounded-xl border border-border bg-[#0A0F1E] p-3.5 font-mono text-[12.5px] text-accent">
        {code.join("\n")}
      </pre>
    );
  }

  return <div>{blocks}</div>;
}
