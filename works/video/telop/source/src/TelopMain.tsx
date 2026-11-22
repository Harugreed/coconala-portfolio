import React from "react";
import { AbsoluteFill, Audio, Img, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import timing from "../public/voice/main/timing.json";
import { pageLen, Strong, toPages, useFonts } from "./common";

// テロップの仕様（works/video/telop/spec.md と同じ値）
export const SPEC = {
  font: "MPLUS1pXB",
  size: 46,            // 1280×720 での文字の大きさ（px）
  maxChars: 20,        // 1行の上限（全角換算）
  fill: "#FFFFFF",
  em: "#FFD43B",       // 強調語の色
  stroke: "#14213D",   // 縁取りの色
  strokeW: 9,          // 縁取りの太さ（px）
  bottom: 54,          // 画面下からの位置（px）
  inFrames: 4,         // 出るときのフェード（フレーム）
  outPad: 0.25,        // 読み終わってから消えるまで（秒）
};
const NAVY = "#14213D", YEL = "#FFD43B", BG = "#EEF2F6";
export const TITLE_SEC = 4, END_SEC = 5;
const FPS = 30;
export const MAIN_FRAMES = Math.ceil((TITLE_SEC + timing.total + END_SEC) * FPS);

type Line = { file: string; text: string; start: number; dur: number };
type Scene = { id: string; start: number; end: number; visual: any; chapter: string | null; lines: Line[] };
const scenes = timing.scenes as Scene[];
const f = (sec: number) => Math.round((sec + TITLE_SEC) * FPS);

/* ---------- テロップ ---------- */
export const Telop: React.FC<{ text: string; local: number; frames: number; spec?: typeof SPEC }> = ({ text, local, frames, spec = SPEC }) => {
  const pages = toPages(text, spec.maxChars);
  const total = pages.reduce((n, p) => n + pageLen(p), 0);
  const speak = Math.max(1, frames - spec.outPad * FPS);
  let acc = 0, idx = 0, pageStart = 0;
  for (let i = 0; i < pages.length; i++) {
    const end = ((acc + pageLen(pages[i])) / total) * speak;
    if (local < end || i === pages.length - 1) { idx = i; pageStart = (acc / total) * speak; break; }
    acc += pageLen(pages[i]);
  }
  const t = local - pageStart;
  const op = interpolate(t, [0, spec.inFrames], [0, 1], { extrapolateRight: "clamp" });
  const y = interpolate(t, [0, spec.inFrames], [10, 0], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: spec.bottom, textAlign: "center", opacity: op, transform: `translateY(${y}px)` }}>
      {pages[idx].map((r, i) => (
        <div key={i} style={{
          fontFamily: spec.font, fontSize: spec.size, lineHeight: 1.32, letterSpacing: "0.02em",
          WebkitTextStroke: `${spec.strokeW}px ${spec.stroke}`, paintOrder: "stroke fill",
          textShadow: "0 4px 10px rgba(0,0,0,.35)"
        }}>
          <Strong parts={r} color={spec.fill} emColor={spec.em} />
        </div>
      ))}
    </div>
  );
};

/* ---------- 章の見出し（左上） ---------- */
const Chapter: React.FC<{ text: string; local: number }> = ({ text, local }) => {
  const x = interpolate(local, [0, 10], [-40, 0], { extrapolateRight: "clamp" });
  const op = interpolate(local, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 0, top: 34, display: "flex", alignItems: "stretch", opacity: op, transform: `translateX(${x}px)` }}>
      <div style={{ width: 10, background: YEL }} />
      <div style={{ background: NAVY, color: "#fff", fontFamily: SPEC.font, fontSize: 24, padding: "10px 22px 11px 16px", letterSpacing: "0.04em" }}>{text}</div>
    </div>
  );
};

/* ---------- 素材映像（6秒ごとに切り替え、ゆっくり寄る） ---------- */
const Clips: React.FC<{ list: string[]; frames: number }> = ({ list, frames }) => {
  const seg = 6 * FPS;
  const n = Math.ceil(frames / seg);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {Array.from({ length: n }, (_, k) => (
        <Sequence key={k} from={k * seg} durationInFrames={Math.min(seg, frames - k * seg)}>
          <KenBurns src={list[k % list.length]} startFrom={Math.floor(k / list.length) * 3 * FPS} seg={seg} />
        </Sequence>
      ))}
      <AbsoluteFill style={{ background: "linear-gradient(to top, rgba(10,18,35,.55), rgba(10,18,35,0) 45%)" }} />
    </AbsoluteFill>
  );
};
const KenBurns: React.FC<{ src: string; startFrom: number; seg: number }> = ({ src, startFrom, seg }) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, seg], [1.0, 1.07]);
  return (
    <AbsoluteFill style={{ transform: `scale(${scale})` }}>
      <OffthreadVideo src={staticFile(`clips/${src}`)} muted startFrom={startFrom} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    </AbsoluteFill>
  );
};

/* ---------- 図解 ---------- */
const Panel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: BG, fontFamily: SPEC.font, color: NAVY }}>{children}</AbsoluteFill>
);
const pop = (frame: number, at: number) => spring({ frame: frame - at, fps: FPS, config: { damping: 14, stiffness: 140 } });

const DiagramFlow: React.FC<{ marks: number[] }> = ({ marks }) => {
  const frame = useCurrentFrame();
  const box = (label: string, sub: string, i: number, x: number, color = "#fff") => {
    const s = pop(frame, marks[i] ?? 0);
    return (
      <div style={{ position: "absolute", left: x, top: 150, width: 300, height: 190, background: color, borderRadius: 14, boxShadow: "0 10px 24px rgba(20,33,61,.12)", padding: "26px 24px", transform: `scale(${s})`, opacity: s }}>
        <div style={{ fontSize: 22, color: "#55627A" }}>{`手順 ${i + 1}`}</div>
        <div style={{ fontSize: 34, marginTop: 6 }}>{label}</div>
        <div style={{ fontSize: 21, marginTop: 10, color: "#3A4660", fontFamily: "sans-serif", fontWeight: 700 }}>{sub}</div>
      </div>
    );
  };
  const arrow = (x: number, i: number) => <div style={{ position: "absolute", left: x, top: 222, fontSize: 52, color: YEL, opacity: pop(frame, (marks[i] ?? 0) + 6) }}>▶</div>;
  const leave = pop(frame, marks[1] + 40);
  return (
    <Panel>
      {box("地図で見つける", "「近くのカフェ」で検索", 0, 80)}
      {arrow(395, 1)}
      {box("ページを開く", "営業時間・写真・口コミを確認", 1, 470)}
      {arrow(785, 2)}
      {box("来店を決める", "情報がそろっていれば来店", 2, 860, "#FFF6CC")}
      <div style={{ position: "absolute", left: 430, top: 365, width: 380, textAlign: "center", fontSize: 26, color: "#B23A2E", opacity: leave, transform: `translateY(${(1 - leave) * 20}px)` }}>情報が足りない → 別の店へ</div>
    </Panel>
  );
};

const DiagramChecklist: React.FC = () => {
  const frame = useCurrentFrame();
  const items = ["店名", "住所", "電話番号", "営業時間", "定休日・祝日の営業"];
  return (
    <Panel>
      <div style={{ position: "absolute", left: 160, top: 100, fontSize: 40 }}>基本情報のチェックリスト</div>
      {items.map((t, i) => {
        const s = pop(frame, 8 + i * 12);
        return (
          <div key={t} style={{ position: "absolute", left: 180, top: 190 + i * 66, display: "flex", alignItems: "center", gap: 22, fontSize: 36, opacity: s, transform: `translateX(${(1 - s) * -30}px)` }}>
            <div style={{ width: 46, height: 46, borderRadius: 8, background: NAVY, color: YEL, display: "grid", placeItems: "center", fontSize: 34 }}>✓</div>{t}
          </div>
        );
      })}
      <div style={{ position: "absolute", right: 120, top: 250, width: 330, padding: 26, borderRadius: 14, background: "#fff", fontSize: 24, lineHeight: 1.55, opacity: pop(frame, 70) }}>
        <div style={{ color: "#B23A2E" }}>更新が止まりやすい</div>
        <div style={{ fontSize: 30, marginTop: 6 }}>定休日・臨時休業</div>
      </div>
    </Panel>
  );
};

const DiagramPhotos: React.FC = () => {
  const frame = useCurrentFrame();
  const cats = [["外観", "roaster.jpg"], ["店内", "table.jpg"], ["商品", "bake.jpg"], ["メニュー", "pour.jpg"]];
  const total = Math.min(20, Math.floor(interpolate(frame, [40, 100], [0, 20], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })));
  return (
    <Panel>
      {cats.map(([t, img], i) => {
        const s = pop(frame, 4 + i * 8);
        return (
          <div key={t} style={{ position: "absolute", left: 80 + i * 285, top: 90, width: 255, opacity: s, transform: `translateY(${(1 - s) * 30}px)` }}>
            <Img src={staticFile(`img/${img}`)} style={{ width: 255, height: 190, objectFit: "cover", borderRadius: 10 }} />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 32, marginTop: 12 }}><span>{t}</span><span style={{ color: "#2A6F97" }}>5枚</span></div>
          </div>
        );
      })}
      <div style={{ position: "absolute", left: 0, right: 0, top: 360, textAlign: "center", fontSize: 40 }}>
        合計 <span style={{ fontSize: 96, color: NAVY, background: `linear-gradient(transparent 62%, ${YEL} 62%)`, padding: "0 10px" }}>{total}</span> 枚
      </div>
    </Panel>
  );
};

const DiagramMetrics: React.FC<{ marks: number[] }> = ({ marks }) => {
  const frame = useCurrentFrame();
  const metrics = [["表示回数", [0.55, 0.62, 0.8]], ["経路の検索", [0.3, 0.42, 0.7]], ["電話", [0.2, 0.24, 0.36]]] as const;
  const at = marks[1] ?? 30;
  return (
    <Panel>
      <div style={{ position: "absolute", left: 120, top: 92, fontSize: 36 }}>月に一度確かめる3つの数字</div>
      {metrics.map(([name, vals], i) => (
        <div key={name} style={{ position: "absolute", left: 140 + i * 350, top: 150, width: 280 }}>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 18, height: 240 }}>
            {vals.map((v, j) => {
              const h = interpolate(frame, [at + i * 10 + j * 6, at + i * 10 + j * 6 + 18], [0, v * 230], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
              return <div key={j} style={{ width: 62, height: h, background: j === 2 ? "#2A6F97" : "#B7C3D3", borderRadius: "6px 6px 0 0" }} />;
            })}
          </div>
          <div style={{ fontSize: 30, marginTop: 12, borderTop: `3px solid ${NAVY}`, paddingTop: 10 }}>{name}</div>
          <div style={{ fontSize: 18, color: "#55627A", fontFamily: "sans-serif" }}>1〜3か月目（イメージ）</div>
        </div>
      ))}
    </Panel>
  );
};

const DiagramSummary: React.FC<{ marks: number[] }> = ({ marks }) => {
  const frame = useCurrentFrame();
  const items = ["基本情報をすべて埋める", "写真を4つの種類でそろえる", "投稿と返信を続ける"];
  return (
    <Panel>
      <div style={{ position: "absolute", left: 120, top: 100, fontSize: 40 }}>まとめ</div>
      {items.map((t, i) => {
        const s = pop(frame, (marks[1] ?? 20) + i * 22);
        return (
          <div key={t} style={{ position: "absolute", left: 140, top: 180 + i * 96, display: "flex", alignItems: "center", gap: 24, fontSize: 42, opacity: s, transform: `translateX(${(1 - s) * -30}px)` }}>
            <div style={{ width: 64, height: 64, borderRadius: 32, background: NAVY, color: YEL, display: "grid", placeItems: "center", fontSize: 36 }}>{i + 1}</div>{t}
          </div>
        );
      })}
    </Panel>
  );
};

/* ---------- 全体 ---------- */
export type MainProps = { mode?: "designed" | "auto"; mute?: boolean };
export const TelopMain: React.FC<MainProps> = ({ mode = "designed", mute = false }) => {
  useFonts();
  const frame = useCurrentFrame();
  const durationInFrames = MAIN_FRAMES;
  const tLocal = frame;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {/* タイトル */}
      <Sequence from={0} durationInFrames={TITLE_SEC * FPS}>
        <AbsoluteFill style={{ background: NAVY, color: "#fff", fontFamily: SPEC.font, justifyContent: "center", paddingLeft: 110 }}>
          <div style={{ fontSize: 26, color: YEL, opacity: interpolate(tLocal, [0, 12], [0, 1]) }}>小さな店の集客</div>
          <div style={{ fontSize: 60, lineHeight: 1.35, marginTop: 14, opacity: interpolate(tLocal, [6, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>Googleマップで<br />見つけてもらう3つの準備</div>
          <div style={{ width: interpolate(tLocal, [14, 40], [0, 520], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }), height: 8, background: YEL, marginTop: 26 }} />
        </AbsoluteFill>
      </Sequence>

      {scenes.map((sc, i) => {
        const from = f(sc.start), dur = Math.max(1, f(sc.end) - from);
        const marks = sc.lines.map((l) => f(l.start) - from);
        const v = sc.visual;
        let body: React.ReactNode = null;
        if (v.type === "clip") {
          const list = [v.src, v.src2].filter(Boolean);
          if (sc.id === "intro") list.push("4915.mp4");
          if (sc.id === "prep1") list.push("817.mp4");
          body = <Clips list={list} frames={dur} />;
        } else if (v.kind === "flow") body = <DiagramFlow marks={marks} />;
        else if (v.kind === "checklist") body = <DiagramChecklist />;
        else if (v.kind === "photos") body = <DiagramPhotos />;
        else if (v.kind === "metrics") body = <DiagramMetrics marks={marks} />;
        else if (v.kind === "summary") body = <DiagramSummary marks={marks} />;
        const prevChapter = i > 0 ? scenes[i - 1].chapter : null;
        return (
          <Sequence key={sc.id} from={from} durationInFrames={dur}>
            {body}
            {sc.chapter && mode === "designed" && <ChapterHost text={sc.chapter} fresh={sc.chapter !== prevChapter} />}
            {sc.chapter !== prevChapter && !mute && <Audio src={staticFile("audio/se-whoosh.mp3")} volume={0.18} />}
          </Sequence>
        );
      })}

      {/* テロップと音声 */}
      {scenes.flatMap((sc) => sc.lines).map((l) => {
        const from = f(l.start);
        const dur = Math.round((l.dur + SPEC.outPad) * FPS);
        return (
          <Sequence key={l.file} from={from} durationInFrames={dur}>
            {!mute && <Audio src={staticFile(`voice/main/${l.file}`)} />}
            {mode === "designed" ? <TelopHost text={l.text} frames={dur} /> : <AutoCaption text={l.text} frames={dur} />}
          </Sequence>
        );
      })}

      {/* 終わり */}
      <Sequence from={durationInFrames - END_SEC * FPS}>
        <AbsoluteFill style={{ background: NAVY, color: "#fff", fontFamily: SPEC.font, justifyContent: "center", alignItems: "center", textAlign: "center" }}>
          <div style={{ fontSize: 44 }}>まず、営業時間と定休日の見直しから</div>
          <div style={{ fontSize: 22, marginTop: 30, opacity: 0.75 }}>自主制作サンプル｜素材映像・音楽：Mixkit　音声合成：Irodori-TTS</div>
        </AbsoluteFill>
      </Sequence>

      {!mute && <Audio src={staticFile("audio/bgm-corporate.mp3")} volume={0.07} loop />}
    </AbsoluteFill>
  );
};

const TelopHost: React.FC<{ text: string; frames: number }> = ({ text, frames }) => {
  const local = useCurrentFrame();
  return <Telop text={text} local={local} frames={frames} />;
};
const ChapterHost: React.FC<{ text: string; fresh: boolean }> = ({ text, fresh }) => {
  const local = useCurrentFrame();
  return <Chapter text={text} local={fresh ? local : 99} />;
};

/* ---------- 比較用：自動字幕のままの表示 ---------- */
const MISHEAR: [RegExp, string][] = [[/Googleマップ/g, "グーグルマップ"], [/口コミ/g, "口込み"], [/空欄/g, "空らん"], [/分かれ目/g, "わかれめ"], [/数秒/g, "数票"]];
export const autoText = (line: string) => {
  let s = line.replace(/\[\[|\]\]/g, "").replace(/[、。「」]/g, " ").replace(/\s+/g, " ").trim();
  for (const [a, b] of MISHEAR) s = s.replace(a, b);
  return s;
};
const AutoCaption: React.FC<{ text: string; frames: number }> = ({ text, frames }) => {
  const frame = useCurrentFrame();
  const words = autoText(text).split(" ");
  const chunks: string[] = [];
  let cur = "";
  for (const w of words) { if ((cur + w).length > 16 && cur) { chunks.push(cur.trim()); cur = ""; } cur += w + " "; }
  if (cur.trim()) chunks.push(cur.trim());
  const idx = Math.min(chunks.length - 1, Math.floor((frame / frames) * chunks.length));
  const shown = [chunks[idx - 1], chunks[idx]].filter(Boolean);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 40, textAlign: "center" }}>
      {shown.map((c, i) => (
        <div key={i}><span style={{ background: "rgba(8,8,8,.75)", color: "#fff", fontFamily: "'Yu Gothic UI', 'Meiryo', sans-serif", fontSize: 28, padding: "2px 8px", lineHeight: 1.5 }}>{c}</span></div>
      ))}
    </div>
  );
};
