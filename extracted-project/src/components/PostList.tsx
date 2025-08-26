import React from 'react'

interface PostListProps {
  className?: string
}

const PostList: React.FC<PostListProps> = ({ className = '' }) => {
  return (
    <div className="p-4 border {className}">
      <h2 className="text-xl font-semibold mb-2">PostList</h2>
      <p className="text-gray-600 dark:text-gray-300">
        This is the PostList component.
      </p>
    </div>
  )
}

export default PostList