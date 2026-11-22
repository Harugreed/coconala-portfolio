import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { useFonts } from "./common";
import { TelopMain, TITLE_SEC } from "./TelopMain";

export const BA_FRAMES = 30 * 30;
const START = TITLE_SEC * 30; // 本編のタイトルの直後から30秒

const Half: React.FC<{ x: number; label: string; sub: string; color: string; mode: "auto" | "designed"; mute: boolean }> = ({ x, label, sub, color, mode, mute }) => (
  <>
    <div style={{ position: "absolute", left: x, top: 150, width: 624, fontFamily: "MPLUS1pXB", color: "#fff" }}>
      <span style={{ background: color, padding: "6px 14px", fontSize: 26 }}>{label}</span>
      <span style={{ marginLeft: 12, fontSize: 18, opacity: 0.8 }}>{sub}</span>
    </div>
    <div style={{ position: "absolute", left: x, top: 204, width: 624, height: 351, overflow: "hidden", border: `4px solid ${color}` }}>
      <div style={{ width: 1280, height: 720, transform: "scale(0.4875)", transformOrigin: "top left" }}>
        <Sequence from={-START} layout="none">
          <TelopMain mode={mode} mute={mute} />
        </Sequence>
      </div>
    </div>
  </>
);

export const BeforeAfter: React.FC = () => {
  useFonts();
  return (
    <AbsoluteFill style={{ background: "#0F1626" }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 50, textAlign: "center", fontFamily: "MPLUS1pXB", color: "#fff", fontSize: 38 }}>同じ映像・同じ音声で、テロップだけを比べる</div>
      <Half x={12} label="Before" sub="自動字幕のまま" color="#6B7280" mode="auto" mute={true} />
      <Half x={644} label="After" sub="デザイン済みテロップ" color="#E0A100" mode="designed" mute={false} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 52, textAlign: "center", fontFamily: "sans-serif", color: "#AEB6C6", fontSize: 20 }}>
        After：句読点で改行・強調語を黄色・縁取りで背景に負けない・章の見出しを表示
      </div>
      <div style={{ position: "absolute", right: 20, bottom: 14, fontFamily: "sans-serif", color: "#6B7280", fontSize: 14 }}>自主制作サンプル</div>
    </AbsoluteFill>
  );
};
