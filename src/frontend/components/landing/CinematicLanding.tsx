"use client";

import Navbar from "./Navbar";
import Hero from "./Hero";
import Pipeline from "./Pipeline";
import Features from "./Features";
import Architecture from "./Architecture";
import JudgePreview from "./JudgePreview";
import Footer from "./Footer";

export default function CinematicLanding() {
  return (
    <main className="min-h-screen overflow-x-hidden bg-[#050816] text-white">
      <Navbar />

      <Hero />

      <Pipeline />

      <Features />

      <Architecture />

      <JudgePreview />

      <Footer />
    </main>
  );
}