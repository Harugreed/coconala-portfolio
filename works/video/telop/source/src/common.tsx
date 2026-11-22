import React, { useEffect, useState } from "react";
import { continueRender, delayRender, staticFile } from "remotion";

// 同梱フォント（すべて SIL Open Font License）
const FONTS = [
  { family: "MPLUS1pXB", file: "fonts/MPLUS1p-ExtraBold.ttf" },
  { family: "ZenMaruBlack", file: "fonts/ZenMaruGothic-Black.ttf" },
  { family: "DelaGothic", file: "fonts/DelaGothicOne-Regular.ttf" },
];

export const useFonts = () => {
  const [handle] = useState(() => delayRender("fonts"));
  useEffect(() => {
    Promise.all(
      FONTS.map(async (f) => {
        const face = new FontFace(f.family, `url(${staticFile(f.file)})`);
        await face.load();
        document.fonts.add(face);
      })
    ).then(() => continueRender(handle));
  }, [handle]);
};

/** [[強調]] を含む文を、テロップ用の部品（強調かどうか）に分ける。文末の「。」は表示しない */
export type Part = { text: string; em: boolean };
export const parseParts = (line: string): Part[] => {
  const s = line.replace(/。$/, "");
  const out: Part[] = [];
  const re = /\[\[(.+?)\]\]/g;
  let last = 0;
  for (const m of s.matchAll(re)) {
    if (m.index! > last) out.push({ text: s.slice(last, m.index), em: false });
    out.push({ text: m[1], em: true });
    last = m.index! + m[0].length;
  }
  if (last < s.length) out.push({ text: s.slice(last), em: false });
  return out;
};

const plain = (parts: Part[]) => parts.map((p) => p.text).join("");

/**
 * 1行の上限（全角換算）を超える文を、読点 → 助詞の後ろ → 中央 の順で探した位置で行に分ける。
 * 単語の途中（強調語の中）では割らない。
 */
export const breakLines = (parts: Part[], max: number): Part[][] => {
  const text = plain(parts);
  if ([...text].length <= max) return [parts];
  const chars = [...text];
  const protectedIdx = new Set<number>();
  let pos = 0;
  for (const p of parts) {
    const n = [...p.text].length;
    if (p.em) for (let i = pos + 1; i < pos + n; i++) protectedIdx.add(i);
    pos += n;
  }
  const target = chars.length / 2;
  const score = (i: number) => Math.abs(i - target);
  const cands = (test: (c: string, i: number) => boolean) =>
    chars.map((c, i) => i + 1).filter((i) => i < chars.length && test(chars[i - 1], i) && !protectedIdx.has(i));
  const period = cands((c) => c === "。");
  const punct = cands((c) => c === "、" || c === "，" || c === "」");
  const particle = cands((c, i) => "はがをにでもへ".includes(c) && i > 2);
  const pick = (arr: number[]) => arr.filter((i) => i >= chars.length * 0.25 && i <= chars.length * 0.75).sort((a, b) => score(a) - score(b))[0];
  const nearest = (arr: number[]) => arr.filter((i) => i >= 2 && i <= chars.length - 2).sort((a, b) => score(a) - score(b))[0];
  let mid = Math.round(target);
  while (protectedIdx.has(mid) && mid < chars.length - 1) mid++;
  const cut = pick(period) ?? pick(punct) ?? pick(particle) ?? nearest([...punct, ...particle]) ?? mid;
  // 部品の配列を cut の位置で2つに分ける
  const a: Part[] = [], b: Part[] = [];
  let k = 0;
  for (const p of parts) {
    const pc = [...p.text];
    const left = Math.max(0, Math.min(pc.length, cut - k));
    if (left > 0) a.push({ text: pc.slice(0, left).join(""), em: p.em });
    if (left < pc.length) b.push({ text: pc.slice(left).join(""), em: p.em });
    k += pc.length;
  }
  if (a.length && /[、。]$/.test(a[a.length - 1].text)) a[a.length - 1].text = a[a.length - 1].text.slice(0, -1);
  return [a, b];
};

export const Strong: React.FC<{ parts: Part[]; color: string; emColor: string; emBg?: string }> = ({ parts, color, emColor, emBg }) => (
  <>
    {parts.map((p, i) => (
      <span key={i} style={p.em ? { color: emColor, background: emBg, padding: emBg ? "0 8px" : undefined } : { color }}>{p.text}</span>
    ))}
  </>
);

/** 上限を超える行がなくなるまで分け、2行ずつのページにする */
export const toPages = (line: string, max: number, perPage = 2): Part[][][] => {
  const split = (parts: Part[]): Part[][] => {
    const len = [...parts.map((p) => p.text).join("")].length;
    if (len <= max) return [parts];
    const [a, b] = breakLines(parts, max);
    if (!b || !b.length) return [a];
    return [...split(a), ...split(b)];
  };
  const rows = split(parseParts(line));
  const pages: Part[][][] = [];
  for (let i = 0; i < rows.length; i += perPage) pages.push(rows.slice(i, i + perPage));
  return pages;
};
export const pageLen = (page: Part[][]) => page.reduce((n, r) => n + [...r.map((p) => p.text).join("")].length, 0);
