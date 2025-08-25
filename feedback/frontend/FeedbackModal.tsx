/**
 * FeedbackModal.tsx
 * React component for collecting user feedback on generated projects
 */

import React, { useState, useEffect } from 'react';
import { X, Star, Send, AlertCircle, CheckCircle } from 'lucide-react';

interface FeedbackModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  generatedFilesCount?: number;
  completionTimeSeconds?: number;
}

interface FeedbackData {
  user_rating: number;
  vibe_alignment_score: number;
  code_quality_score: number;
  usability_score: number;
  comments: string;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  projectId,
  isOpen,
  onClose,
  generatedFilesCount,
  completionTimeSeconds
}) => {
  const [feedback, setFeedback] = useState<FeedbackData>({
    user_rating: 5,
    vibe_alignment_score: 8,
    code_quality_score: 8,
    usability_score: 8,
    comments: ''
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setFeedback({
        user_rating: 5,
        vibe_alignment_score: 8,
        code_quality_score: 8,
        usability_score: 8,
        comments: ''
      });
      setSubmitStatus('idle');
      setErrorMessage('');
    }
  }, [isOpen]);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitStatus('idle');

    try {
      const response = await fetch('/api/feedback/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: projectId,
          user_rating: feedback.user_rating,
          vibe_alignment_score: feedback.vibe_alignment_score,
          code_quality_score: feedback.code_quality_score,
          usability_score: feedback.usability_score,
          comments: feedback.comments.trim() || null,
          generated_files_count: generatedFilesCount,
          completion_time_seconds: completionTimeSeconds,
          user_session_id: sessionStorage.getItem('user_session_id') || undefined
        })
      });

      if (response.ok) {
        setSubmitStatus('success');
        setTimeout(() => {
          onClose();
        }, 2000);
      } else {
        const errorData = await response.json();
        setSubmitStatus('error');
        setErrorMessage(errorData.detail || 'Failed to submit feedback');
      }
    } catch (error) {
      setSubmitStatus('error');
      setErrorMessage('Network error - please try again');
      console.error('Feedback submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStars = (value: number, onChange: (value: number) => void) => {
    return (
      <div className="flex space-x-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => onChange(star)}
            className={`text-2xl transition-colors ${
              star <= value 
                ? 'text-yellow-500 hover:text-yellow-600' 
                : 'text-gray-300 hover:text-gray-400'
            }`}
          >
            <Star fill={star <= value ? 'currentColor' : 'none'} />
          </button>
        ))}
      </div>
    );
  };

  const renderSlider = (
    value: number, 
    onChange: (value: number) => void, 
    min: number = 1, 
    max: number = 10
  ) => {
    return (
      <div className="flex items-center space-x-3">
        <span className="text-sm text-gray-500 w-8">{min}</span>
        <input
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={(e) => onChange(parseInt(e.target.value))}
          className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
        <span className="text-sm text-gray-500 w-8">{max}</span>
        <span className="text-lg font-semibold text-blue-600 w-8">{value}</span>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">Rate Your Generated Project</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {submitStatus === 'success' ? (
            <div className="text-center py-8">
              <CheckCircle size={64} className="text-green-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-green-700 mb-2">
                Thank you for your feedback!
              </h3>
              <p className="text-gray-600">
                Your feedback helps us improve the Multi-Agent Code Generation System.
              </p>
            </div>
          ) : (
            <>
              {/* Overall Rating */}
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-3">
                  Overall Rating
                </label>
                {renderStars(feedback.user_rating, (value) => 
                  setFeedback(prev => ({ ...prev, user_rating: value }))
                )}
                <p className="text-sm text-gray-500 mt-1">
                  How would you rate this generated project overall?
                </p>
              </div>

              {/* Vibe Alignment */}
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-3">
                  Vibe Alignment: {feedback.vibe_alignment_score}/10
                </label>
                {renderSlider(
                  feedback.vibe_alignment_score,
                  (value) => setFeedback(prev => ({ ...prev, vibe_alignment_score: value }))
                )}
                <p className="text-sm text-gray-500 mt-1">
                  How well did the output match your intended vibe or vision?
                </p>
              </div>

              {/* Code Quality */}
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-3">
                  Code Quality: {feedback.code_quality_score}/10
                </label>
                {renderSlider(
                  feedback.code_quality_score,
                  (value) => setFeedback(prev => ({ ...prev, code_quality_score: value }))
                )}
                <p className="text-sm text-gray-500 mt-1">
                  How would you rate the quality of the generated code?
                </p>
              </div>

              {/* Usability */}
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-3">
                  Usability: {feedback.usability_score}/10
                </label>
                {renderSlider(
                  feedback.usability_score,
                  (value) => setFeedback(prev => ({ ...prev, usability_score: value }))
                )}
                <p className="text-sm text-gray-500 mt-1">
                  How practical and usable is the generated project?
                </p>
              </div>

              {/* Comments */}
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-3">
                  Additional Comments (Optional)
                </label>
                <textarea
                  value={feedback.comments}
                  onChange={(e) => setFeedback(prev => ({ ...prev, comments: e.target.value }))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={4}
                  placeholder="Share any specific feedback, suggestions, or issues you encountered..."
                  maxLength={2000}
                />
                <p className="text-sm text-gray-500 mt-1">
                  {feedback.comments.length}/2000 characters
                </p>
              </div>

              {/* Project Info */}
              {(generatedFilesCount || completionTimeSeconds) && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-700 mb-2">Project Details</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    {generatedFilesCount && (
                      <p>Files generated: {generatedFilesCount}</p>
                    )}
                    {completionTimeSeconds && (
                      <p>Generation time: {Math.round(completionTimeSeconds)}s</p>
                    )}
                    <p>Project ID: {projectId.slice(0, 8)}...</p>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {submitStatus === 'error' && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-2">
                  <AlertCircle size={20} className="text-red-500" />
                  <span className="text-red-700">{errorMessage}</span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {submitStatus !== 'success' && (
          <div className="flex justify-end space-x-3 p-6 border-t bg-gray-50">
            <button
              onClick={onClose}
              className="px-6 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <Send size={16} />
                  <span>Submit Feedback</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default FeedbackModal;