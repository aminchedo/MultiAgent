import React from "react"
import "./index.css"
import Footer from "./components/Footer"
import Header from "./components/Header"
import Contact from "./components/Contact"
import Hero from "./components/Hero"
import ProjectCard from "./components/ProjectCard"

function App() {
  return (
    <div className="light min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4">
      <Footer />
      <Header />
      <Contact />
      <Hero />
      <ProjectCard />
      </div>
    </div>
  )
}

export default App