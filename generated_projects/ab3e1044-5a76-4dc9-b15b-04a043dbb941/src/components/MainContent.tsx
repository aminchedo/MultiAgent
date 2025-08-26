import React from 'react'

interface MainContentProps {
  className?: string
}

const MainContent: React.FC<MainContentProps> = ({ className = '' }) => {
  return (
    <div className="p-4 rounded-lg shadow-sm {className}">
      <h2 className="text-xl font-semibold mb-2">MainContent</h2>
      <p className="text-gray-600 dark:text-gray-300">
        This is the MainContent component.
      </p>
    </div>
  )
}

export default MainContent