import React from 'react'

interface PostDetailProps {
  className?: string
}

const PostDetail: React.FC<PostDetailProps> = ({ className = '' }) => {
  return (
    <div className="p-4 border {className}">
      <h2 className="text-xl font-semibold mb-2">PostDetail</h2>
      <p className="text-gray-600 dark:text-gray-300">
        This is the PostDetail component.
      </p>
    </div>
  )
}

export default PostDetail