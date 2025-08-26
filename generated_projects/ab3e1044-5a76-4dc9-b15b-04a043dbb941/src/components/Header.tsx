import React from 'react'

interface HeaderProps {
  className?: string
}

const Header: React.FC<HeaderProps> = ({ className = '' }) => {
  return (
    <div className="p-4 rounded-lg shadow-sm {className}">
      <h2 className="text-xl font-semibold mb-2">Header</h2>
      <p className="text-gray-600 dark:text-gray-300">
        This is the Header component.
      </p>
    </div>
  )
}

export default Header