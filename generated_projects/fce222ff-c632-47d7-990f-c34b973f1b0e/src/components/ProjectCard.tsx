import React from 'react'

interface ProjectCardProps {
  className?: string
}

const ProjectCard: React.FC<ProjectCardProps> = ({ className = '' }) => {
  return (
    <div className="p-4 rounded-lg shadow-sm {className}">
      <h2 className="text-xl font-semibold mb-2">ProjectCard</h2>
      <p className="text-gray-600 dark:text-gray-300">
        This is the ProjectCard component.
      </p>
    </div>
  )
}

export default ProjectCard