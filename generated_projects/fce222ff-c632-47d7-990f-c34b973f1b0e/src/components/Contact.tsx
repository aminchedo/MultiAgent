import React from 'react'

interface ContactProps {
  className?: string
}

const Contact: React.FC<ContactProps> = ({ className = '' }) => {
  return (
    <div className="p-4 rounded-lg shadow-sm {className}">
      <h2 className="text-xl font-semibold mb-2">Contact</h2>
      <p className="text-gray-600 dark:text-gray-300">
        This is the Contact component.
      </p>
    </div>
  )
}

export default Contact