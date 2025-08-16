"use client"
import { useState } from 'react'

interface VibeInputProps {
	onSubmit: (description: string) => void
}

export const VibeInput: React.FC<VibeInputProps> = ({ onSubmit }) => {
	const [description, setDescription] = useState('')

	return (
		<div className="vibe-input p-6 border rounded-lg">
			<h2 className="text-2xl font-bold mb-4">Describe Your Project Vibe</h2>
			<textarea
				placeholder="I want to build a social media app with dark mode and animations..."
				value={description}
				onChange={(e) => setDescription(e.target.value)}
				className="min-h-32 mb-4 w-full p-3 border rounded"
			/>
			<button
				onClick={() => onSubmit(description)}
				disabled={!description.trim()}
				className="w-full px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
			>
				Generate Project 🚀
			</button>
		</div>
	)
}