import React from "react";
import { Composition } from "remotion";
import { MAIN_FRAMES, TelopMain } from "./TelopMain";
import { BeforeAfter, BA_FRAMES } from "./BeforeAfter";
import { ReelGourmet, ReelBiz, ReelQuiz, REEL_FRAMES } from "./Reels";

export const Root: React.FC = () => (
  <>
    <Composition id="TelopMain" component={TelopMain} durationInFrames={MAIN_FRAMES} fps={30} width={1280} height={720} />
    <Composition id="BeforeAfter" component={BeforeAfter} durationInFrames={BA_FRAMES} fps={30} width={1280} height={720} />
    <Composition id="ReelGourmet" component={ReelGourmet} durationInFrames={REEL_FRAMES.gourmet} fps={30} width={1080} height={1920} />
    <Composition id="ReelBiz" component={ReelBiz} durationInFrames={REEL_FRAMES.biz} fps={30} width={1080} height={1920} />
    <Composition id="ReelQuiz" component={ReelQuiz} durationInFrames={REEL_FRAMES.quiz} fps={30} width={1080} height={1920} />
  </>
);
