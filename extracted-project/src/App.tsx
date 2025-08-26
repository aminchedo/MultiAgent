import React from "react"
import PostDetail from "./components/PostDetail"
import PostList from "./components/PostList"
import Footer from "./components/Footer"
import Header from "./components/Header"

function App() {
  return (
    <div className="light min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4">
      <PostDetail />
      <PostList />
      <Footer />
      <Header />
      </div>
    </div>
  )
}

export default App