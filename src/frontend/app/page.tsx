import Navbar from "@/components/landing/Navbar";
import Hero from "@/components/landing/Hero";
import Pipeline from "@/components/landing/Pipeline";
import Architecture from "@/components/landing/Architecture";
import DirectorMonitor from "@/components/landing/DirectorMonitor";
import TechnologyStack from "@/components/landing/TechnologyStack";
import UploadPreview from "@/components/landing/Uploadpreview";
import FooterPremium from "@/components/landing/FooterPremium";

export default function Home() {
  return (
    <>
      <Navbar />
      <Hero />
      <Pipeline />
      <Architecture />
      <DirectorMonitor />
      <TechnologyStack />
      <UploadPreview />
      <FooterPremium />
    </>
  );
}