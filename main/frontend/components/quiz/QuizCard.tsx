'use client';

import { motion } from 'framer-motion';
import { QuizQuestion } from './quizData';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid';

interface QuizCardProps {
  question: QuizQuestion;
  currentQuestion: number;
  totalQuestions: number;
  selectedAnswer: number | null;
  showFeedback: boolean;
  onSelectAnswer: (answerIndex: number) => void;
  onNext: () => void;
}

export default function QuizCard({
  question,
  currentQuestion,
  totalQuestions,
  selectedAnswer,
  showFeedback,
  onSelectAnswer,
  onNext,
}: QuizCardProps) {
  return (
    <motion.div
      key={question.id}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-8 border border-slate-700/50 shadow-xl"
    >
      {/* Header: Progress */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-400" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
            Question {currentQuestion} of {totalQuestions}
          </span>
          <span className="px-2 py-1 text-xs font-medium rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            {question.category}
          </span>
        </div>
      </div>

      {/* Progress Dots */}
      <div className="flex gap-2 mb-8">
        {Array.from({ length: totalQuestions }).map((_, index) => (
          <div
            key={index}
            className={`h-2 rounded-full transition-all duration-300 ${index < currentQuestion - 1
                ? 'bg-cyan-500 w-4'
                : index === currentQuestion - 1
                  ? 'bg-cyan-400 w-6'
                  : 'bg-gray-600 w-4'
              }`}
          />
        ))}
      </div>

      {/* Question */}
      <h3
        className="text-xl font-semibold text-white mb-8 leading-relaxed"
        style={{ fontFamily: 'Space Grotesk, sans-serif' }}
      >
        {question.question}
      </h3>

      {/* Answer Options */}
      <div className="space-y-3 mb-8">
        {question.options.map((option, index) => {
          const isSelected = selectedAnswer === index;
          const isCorrect = index === question.correctAnswer;

          let cardStyle = 'bg-slate-700/50 text-slate-200 border-slate-600/50';
          let iconStyle = 'border-slate-400';

          if (showFeedback) {
            if (isCorrect) {
              cardStyle = 'bg-emerald-500/10 border-emerald-500/50 text-emerald-100 shadow-[0_0_15px_rgba(16,185,129,0.2)]';
              iconStyle = 'border-emerald-400 bg-emerald-400 text-white';
            } else if (isSelected && !isCorrect) {
              cardStyle = 'bg-red-500/10 border-red-500/50 text-red-100';
              iconStyle = 'border-red-400 bg-red-400 text-white';
            } else {
              cardStyle = 'bg-slate-800/30 text-slate-500 border-slate-700/30 opacity-60';
              iconStyle = 'border-slate-600';
            }
          } else if (isSelected) {
            cardStyle = 'bg-cyan-600 text-white border-cyan-500 shadow-lg shadow-cyan-500/30';
            iconStyle = 'border-white bg-white';
          }

          return (
            <motion.button
              key={index}
              onClick={() => !showFeedback && onSelectAnswer(index)}
              disabled={showFeedback}
              whileHover={!showFeedback ? { scale: 1.02 } : {}}
              whileTap={!showFeedback ? { scale: 0.98 } : {}}
              className={`
                w-full p-4 text-left rounded-lg transition-all duration-200 border-2
                ${cardStyle}
              `}
              style={{ fontFamily: 'Space Grotesk, sans-serif' }}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`
                  w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors
                  ${iconStyle}
                `}
                >
                  {showFeedback && isCorrect && <CheckCircleIcon className="w-4 h-4" />}
                  {showFeedback && isSelected && !isCorrect && <XCircleIcon className="w-4 h-4" />}
                  {!showFeedback && isSelected && <div className="w-3 h-3 rounded-full bg-cyan-600" />}
                </div>
                <span className="flex-1 font-medium">{option}</span>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Feedback / Explanation */}
      {showFeedback && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 p-4 rounded-lg bg-cyan-900/20 border border-cyan-500/30"
        >
          <div className="flex items-start gap-3">
            <div className="mt-1">
              <div className="p-1 bg-cyan-500/20 rounded-full">
                <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-bold text-cyan-400 mb-1">Explanation</h4>
              <p className="text-sm text-slate-300 leading-relaxed">
                {question.explanation}
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Next Button */}
      {showFeedback && (
        <div className="flex justify-end animate-fade-in">
          <motion.button
            onClick={onNext}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-8 py-3 rounded-lg font-medium transition-all duration-200 bg-cyan-600 text-white hover:bg-cyan-500 shadow-lg shadow-cyan-500/30 flex items-center gap-2"
            style={{ fontFamily: 'Space Grotesk, sans-serif' }}
          >
            {currentQuestion === totalQuestions ? 'Finish Quiz' : 'Next Question'}
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </motion.button>
        </div>
      )}
    </motion.div>
  );
}
