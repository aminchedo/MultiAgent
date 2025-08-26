import React from 'react'

interface FooterProps {
  className?: string
}

const Footer: React.FC<FooterProps> = ({ className = '' }) => {
  return (
    <div className="p-4 border {className}">
      <h2 className="text-xl font-semibold mb-2">Footer</h2>
      <p className="text-gray-600 dark:text-gray-300">
        This is the Footer component.
      </p>
    </div>
  )
}

export default Footer