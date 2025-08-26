import React from 'react'

interface SidebarProps {
  className?: string
}

const Sidebar: React.FC<SidebarProps> = ({ className = '' }) => {
  return (
    <div className="p-4 rounded-lg shadow-sm {className}">
      <h2 className="text-xl font-semibold mb-2">Sidebar</h2>
      <p className="text-gray-600 dark:text-gray-300">
        This is the Sidebar component.
      </p>
    </div>
  )
}

export default Sidebar