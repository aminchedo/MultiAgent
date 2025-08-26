import React from "react"
import "./index.css"
import Header from "./components/Header"
import MainContent from "./components/MainContent"
import Sidebar from "./components/Sidebar"

function App() {
  return (
    <div className="light min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4">
      <Header />
      <MainContent />
      <Sidebar />
      </div>
    </div>
  )
}

export default App