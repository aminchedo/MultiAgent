import React from "react"
import "./index.css"
import MainContent from "./components/MainContent"
import Header from "./components/Header"
import Sidebar from "./components/Sidebar"

function App() {
  return (
    <div className="dark min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4">
      <MainContent />
      <Header />
      <Sidebar />
      </div>
    </div>
  )
}

export default App