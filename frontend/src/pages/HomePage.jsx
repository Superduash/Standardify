import { HeroSection } from '../components/home/HeroSection'
import { HowItWorksSection } from '../components/home/HowItWorksSection'
import { FeatureHighlights } from '../components/home/FeatureHighlights'
import { EvidenceSection } from '../components/home/EvidenceSection'

export function HomePage() {
  return (
    <>
      <HeroSection />
      <HowItWorksSection />
      <FeatureHighlights />
      <EvidenceSection />
    </>
  )
}

export default HomePage
