'use client';

import { motion } from 'framer-motion';
import { QuizQuestion } from './quizData';

interface QuizCardProps {
  question: QuizQuestion;
  currentQuestion: number;
  totalQuestions: number;
  selectedAnswer: number | null;
  onSelectAnswer: (answerIndex: number) => void;
  onNext: () => void;
}

export default function QuizCard({
  question,
  currentQuestion,
  totalQuestions,
  selectedAnswer,
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
            className={`h-2 rounded-full transition-all duration-300 ${
              index < currentQuestion - 1
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
        {question.options.map((option, index) => (
          <motion.button
            key={index}
            onClick={() => onSelectAnswer(index)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className={`
              w-full p-4 text-left rounded-lg transition-all duration-200
              ${
                selectedAnswer === index
                  ? 'bg-cyan-600 text-white border-cyan-500 border-2 shadow-lg shadow-cyan-500/30'
                  : 'bg-slate-700/50 text-slate-200 border border-slate-600/50 hover:bg-slate-600/50 hover:border-slate-500/50'
              }
            `}
            style={{ fontFamily: 'Space Grotesk, sans-serif' }}
          >
            <div className="flex items-center gap-3">
              <div
                className={`
                w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0
                ${
                  selectedAnswer === index
                    ? 'border-white bg-white'
                    : 'border-slate-400'
                }
              `}
              >
                {selectedAnswer === index && (
                  <div className="w-3 h-3 rounded-full bg-cyan-600" />
                )}
              </div>
              <span className="flex-1">{option}</span>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Next Button */}
      <div className="flex justify-end">
        <motion.button
          onClick={onNext}
          disabled={selectedAnswer === null}
          whileHover={selectedAnswer !== null ? { scale: 1.05 } : {}}
          whileTap={selectedAnswer !== null ? { scale: 0.95 } : {}}
          className={`
            px-8 py-3 rounded-lg font-medium transition-all duration-200
            ${
              selectedAnswer !== null
                ? 'bg-cyan-600 text-white hover:bg-cyan-500 shadow-lg shadow-cyan-500/30 cursor-pointer'
                : 'bg-slate-700/30 text-slate-500 cursor-not-allowed'
            }
          `}
          style={{ fontFamily: 'Space Grotesk, sans-serif' }}
        >
          {currentQuestion === totalQuestions ? 'See Results' : 'Next Question'} →
        </motion.button>
      </div>
    </motion.div>
  );
}
