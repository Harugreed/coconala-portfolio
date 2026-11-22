import React from "react";
import { AbsoluteFill, Audio, Img, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame } from "remotion";
import biz from "../public/voice/biz/timing.json";
import { Strong, toPages, useFonts } from "./common";

const FPS = 30;
export const REEL_FRAMES = { gourmet: 20 * FPS, biz: Math.ceil((biz.total + 1.2) * FPS), quiz: 22 * FPS };
const SAMPLE: React.CSSProperties = { position: "absolute", right: 28, bottom: 24, color: "rgba(255,255,255,.7)", fontFamily: "sans-serif", fontSize: 22 };

const Cover: React.FC<{ src: string; kind: "clip" | "img"; startFrom?: number; zoom?: [number, number]; frames: number; filter?: string }> = ({ src, kind, startFrom = 0, zoom = [1.05, 1.15], frames, filter }) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, frames], zoom);
  const style: React.CSSProperties = { width: "100%", height: "100%", objectFit: "cover", filter };
  return (
    <AbsoluteFill style={{ transform: `scale(${scale})` }}>
      {kind === "clip" ? <OffthreadVideo src={staticFile(`clips/${src}`)} muted startFrom={startFrom} style={style} /> : <Img src={staticFile(`img/${src}`)} style={style} />}
    </AbsoluteFill>
  );
};

/* ============ 1. グルメ紹介：2秒前後で切り替え、角丸の札で品名と価格 ============ */
const CUTS = [
  { src: "3572.mp4", kind: "clip", tag: "若葉台の焙煎所カフェ", sub: "白杢珈琲" },
  { src: "roaster.jpg", kind: "img", tag: "焙煎は 月・木・土", sub: "店内の5kg焙煎機" },
  { src: "222.mp4", kind: "clip", tag: "本日のドリップ", price: "520円" },
  { src: "3577.mp4", kind: "clip", tag: "カフェラテ", price: "600円" },
  { src: "bake.jpg", kind: "img", tag: "焦がしバターのフィナンシェ", price: "320円" },
  { src: "3581.mp4", kind: "clip", tag: "焼き上がりは 11:00", sub: "売り切れ次第終了" },
  { src: "table.jpg", kind: "img", tag: "8:00〜17:00", sub: "火曜・第3水曜休み" },
] as const;
const CUT = Math.floor((20 * FPS) / CUTS.length);

const Tag: React.FC<{ c: (typeof CUTS)[number] }> = ({ c }) => {
  const frame = useCurrentFrame();
  const s = spring({ frame, fps: FPS, config: { damping: 11, stiffness: 160 } });
  return (
    <div style={{ position: "absolute", left: 70, right: 70, bottom: 420, display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 18, transform: `scale(${0.7 + 0.3 * s})`, transformOrigin: "left bottom", opacity: s }}>
      <div style={{ background: "#FFFFFF", color: "#2B211B", fontFamily: "ZenMaruBlack", fontSize: 66, lineHeight: 1.25, padding: "18px 34px", borderRadius: 999, boxShadow: "0 10px 30px rgba(0,0,0,.3)" }}>{c.tag}</div>
      {"price" in c && <div style={{ background: "#2C6670", color: "#fff", fontFamily: "ZenMaruBlack", fontSize: 84, padding: "8px 34px", borderRadius: 999 }}>{c.price}</div>}
      {"sub" in c && <div style={{ background: "rgba(43,33,27,.85)", color: "#fff", fontFamily: "ZenMaruBlack", fontSize: 44, padding: "12px 28px", borderRadius: 999 }}>{c.sub}</div>}
    </div>
  );
};

export const ReelGourmet: React.FC = () => {
  useFonts();
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {CUTS.map((c, i) => (
        <Sequence key={i} from={i * CUT} durationInFrames={i === CUTS.length - 1 ? 20 * FPS - i * CUT : CUT}>
          <Cover src={c.src} kind={c.kind} frames={CUT} filter="saturate(1.15) brightness(1.05)" />
          <AbsoluteFill style={{ background: "linear-gradient(to top, rgba(0,0,0,.45), rgba(0,0,0,0) 50%)" }} />
          <Tag c={c} />
          <Audio src={staticFile("audio/se-pop.mp3")} volume={0.5} />
        </Sequence>
      ))}
      <div style={{ position: "absolute", left: 70, top: 120, fontFamily: "ZenMaruBlack", color: "#fff", fontSize: 40, textShadow: "0 2px 12px rgba(0,0,0,.5)" }}>カフェ紹介 #1</div>
      <Audio src={staticFile("audio/bgm-cafe.mp3")} volume={0.35} />
      <div style={SAMPLE}>自主制作サンプル</div>
    </AbsoluteFill>
  );
};

/* ============ 2. ビジネスノウハウ：黒地に大きな文字、文ごとにカット、上に進行バー ============ */
type Line = { file: string; text: string; start: number; dur: number };
const BIZ_BG = ["img/roaster.jpg", "img/table.jpg", "img/bake.jpg", "img/pour.jpg", "img/table.jpg"];

const BizText: React.FC<{ text: string; dur: number }> = ({ text, dur }) => {
  const frame = useCurrentFrame();
  const rows = toPages(text, 10, 99)[0];
  return (
    <div style={{ position: "absolute", left: 80, right: 80, top: 640, fontFamily: "MPLUS1pXB", fontSize: 84, lineHeight: 1.3, color: "#fff" }}>
      {rows.map((r, i) => {
        const at = i * Math.min(8, (dur * FPS) / rows.length / 2);
        const s = spring({ frame: frame - at, fps: FPS, config: { damping: 16, stiffness: 180 } });
        return (
          <div key={i} style={{ opacity: s, transform: `translateY(${(1 - s) * 30}px)` }}>
            <Strong parts={r} color="#FFFFFF" emColor="#111" emBg="#FFD43B" />
          </div>
        );
      })}
    </div>
  );
};

export const ReelBiz: React.FC = () => {
  useFonts();
  const frame = useCurrentFrame();
  const lines = biz.scenes.flatMap((s) => s.lines) as Line[];
  const total = REEL_FRAMES.biz;
  return (
    <AbsoluteFill style={{ background: "#111" }}>
      {lines.map((l, i) => {
        const from = Math.round(l.start * FPS);
        const to = i + 1 < lines.length ? Math.round(lines[i + 1].start * FPS) : total;
        return (
          <Sequence key={l.file} from={from} durationInFrames={to - from}>
            <AbsoluteFill style={{ opacity: 0.32 }}><Cover src={BIZ_BG[i].replace("img/", "")} kind="img" frames={to - from} zoom={[1.1, 1.2]} filter="blur(6px) grayscale(.4)" /></AbsoluteFill>
            <Audio src={staticFile(`voice/biz/${l.file}`)} />
            <Audio src={staticFile("audio/se-whoosh.mp3")} volume={0.15} />
            <BizText text={l.text} dur={l.dur} />
            <div style={{ position: "absolute", left: 80, top: 470, fontFamily: "MPLUS1pXB", fontSize: 40, color: "#FFD43B" }}>{["Q", "1", "2", "3", "★"][i]}</div>
          </Sequence>
        );
      })}
      <div style={{ position: "absolute", left: 80, top: 230, fontFamily: "MPLUS1pXB", fontSize: 46, color: "#fff", borderLeft: "10px solid #FFD43B", paddingLeft: 22, lineHeight: 1.3 }}>小さな店の集客メモ<br /><span style={{ fontSize: 34, opacity: 0.7 }}>Googleマップの写真</span></div>
      <div style={{ position: "absolute", left: 0, top: 0, height: 14, width: `${(frame / total) * 100}%`, background: "#FFD43B" }} />
      <Audio src={staticFile("audio/bgm-digital.mp3")} volume={0.08} />
      <div style={SAMPLE}>自主制作サンプル｜音声合成：Irodori-TTS</div>
    </AbsoluteFill>
  );
};

/* ============ 3. エンタメ：3択クイズ、カウントダウン、正解で揺れと効果音 ============ */
export const ReelQuiz: React.FC = () => {
  useFonts();
  const frame = useCurrentFrame();
  const Q = 0, OPT = 2.5 * FPS, CD = 7 * FPS, REVEAL = 11 * FPS, INFO = 15 * FPS;
  const opts = [["A", "黒"], ["B", "緑"], ["C", "赤"]];
  const shake = frame >= REVEAL && frame < REVEAL + 12 ? Math.sin(frame * 2.2) * 14 : 0;
  const count = frame >= CD && frame < REVEAL ? 3 - Math.floor((frame - CD) / FPS) : null;
  return (
    <AbsoluteFill style={{ background: "#FFF2C6", fontFamily: "DelaGothic", color: "#1E1E1E", transform: `translateX(${shake}px)` }}>
      <AbsoluteFill style={{ opacity: 0.22 }}><Cover src="3572.mp4" kind="clip" frames={22 * FPS} zoom={[1.2, 1.3]} /></AbsoluteFill>
      <div style={{ position: "absolute", left: 60, right: 60, top: 170, background: "#1E1E1E", color: "#FFF2C6", padding: "40px 44px", borderRadius: 28, transform: `rotate(-2deg) scale(${spring({ frame, fps: FPS, config: { damping: 10 } })})` }}>
        <div style={{ fontSize: 48, color: "#FF6B3D" }}>コーヒー豆クイズ</div>
        <div style={{ fontSize: 76, lineHeight: 1.3, marginTop: 16 }}>焼く前の生豆は<br />何色？</div>
      </div>
      {opts.map(([k, v], i) => {
        const s = spring({ frame: frame - OPT - i * 8, fps: FPS, config: { damping: 12 } });
        const correct = k === "B" && frame >= REVEAL;
        const dim = k !== "B" && frame >= REVEAL;
        return (
          <div key={k} style={{ position: "absolute", left: 90, right: 90, top: 760 + i * 200, height: 160, borderRadius: 24, background: correct ? "#2FA36B" : "#fff", color: correct ? "#fff" : "#1E1E1E", border: "6px solid #1E1E1E", display: "flex", alignItems: "center", gap: 36, paddingLeft: 40, fontSize: 80, opacity: dim ? 0.35 : s, transform: `translateX(${(1 - s) * 200}px) scale(${correct ? 1.06 : 1})`, boxShadow: "10px 10px 0 #1E1E1E" }}>
            <span style={{ fontSize: 60, color: correct ? "#fff" : "#FF6B3D" }}>{k}</span>{v}
            {correct && <span style={{ marginLeft: "auto", marginRight: 40, fontSize: 70 }}>正解</span>}
          </div>
        );
      })}
      {count !== null && (
        <div style={{ position: "absolute", left: 0, right: 0, top: 1420, textAlign: "center", fontSize: 220, color: "#FF6B3D", transform: `scale(${1.4 - ((frame - CD) % FPS) / FPS * 0.4})` }}>{count}</div>
      )}
      {frame >= INFO && (
        <div style={{ position: "absolute", left: 70, right: 70, top: 1400, background: "#1E1E1E", color: "#fff", borderRadius: 24, padding: "34px 40px", fontFamily: "ZenMaruBlack", fontSize: 48, lineHeight: 1.45, opacity: spring({ frame: frame - INFO, fps: FPS }) }}>
          生豆はうすい緑色。<br />焙煎すると茶色になり、<br />深く焼くほど黒に近づきます。
        </div>
      )}
      <Sequence from={OPT}><Audio src={staticFile("audio/se-pop.mp3")} volume={0.5} /></Sequence>
      <Sequence from={CD} durationInFrames={REVEAL - CD}><Audio src={staticFile("audio/se-suspense.mp3")} volume={0.35} /></Sequence>
      <Sequence from={REVEAL}><Audio src={staticFile("audio/se-correct.mp3")} volume={0.6} /></Sequence>
      <Audio src={staticFile("audio/bgm-pop.mp3")} volume={0.12} />
      <div style={{ ...SAMPLE, color: "rgba(30,30,30,.6)" }}>自主制作サンプル</div>
    </AbsoluteFill>
  );
};
