'use client';

import { motion } from 'framer-motion';
import { QuizQuestion } from './quizData';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid';
import CountUp from './CountUp';

interface QuizResultsProps {
  questions: QuizQuestion[];
  userAnswers: (number | null)[];
  onRetake: () => void;
}

function getScoreLabel(score: number): string {
  if (score >= 90) return 'Validation Expert';
  if (score >= 75) return 'Compliance Professional';
  if (score >= 60) return 'Competent Practitioner';
  return 'Needs Review';
}

function getAchievements(score: number, correctAnswers: number): string[] {
  const achievements: string[] = [];
  if (score === 100) achievements.push('Perfect Score');
  if (score >= 90) achievements.push('GAMP-5 Expert');
  if (correctAnswers >= 7) achievements.push('Consistent Performance');
  return achievements;
}

export default function QuizResults({ questions, userAnswers, onRetake }: QuizResultsProps) {
  const correctCount = userAnswers.filter(
    (answer, index) => answer === questions[index].correctAnswer
  ).length;
  const accuracy = Math.round((correctCount / questions.length) * 100);
  const achievements = getAchievements(accuracy, correctCount);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Score Summary Card with Radial Progress */}
      <div className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-8 border border-slate-700/50 shadow-xl text-center">
        {/* Radial Progress Ring */}
        <motion.div
          className="flex justify-center mb-8"
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ duration: 0.8, delay: 0.2, type: 'spring', stiffness: 200 }}
        >
          <div className="relative w-32 h-32">
            {/* Background ring */}
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="64"
                cy="64"
                r="56"
                fill="none"
                stroke="#1e293b"
                strokeWidth="8"
              />
              {/* Progress ring */}
              <motion.circle
                cx="64"
                cy="64"
                r="56"
                fill="none"
                stroke="#06b6d4"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray="351.86"
                initial={{ strokeDashoffset: 351.86 }}
                animate={{ strokeDashoffset: 351.86 * (1 - accuracy / 100) }}
                transition={{ duration: 1.5, delay: 0.5, ease: 'easeOut' }}
              />
            </svg>

            {/* Checkmark icon */}
            <motion.div
              className="absolute inset-0 flex items-center justify-center"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.4, delay: 1 }}
            >
              <svg className="w-16 h-16 text-cyan-400" fill="none" viewBox="0 0 24 24">
                <path
                  d="M9 12l2 2 4-4"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </motion.div>
          </div>
        </motion.div>

        {/* Score Display */}
        <div className="text-center">
          <motion.h2
            className="font-display text-5xl font-bold text-white mb-2"
            style={{ fontFamily: 'Space Grotesk, sans-serif' }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
          >
            <CountUp end={accuracy} duration={2} />%
          </motion.h2>

          <motion.p
            className="text-2xl text-gray-300 font-semibold"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 1 }}
          >
            {getScoreLabel(accuracy)}
          </motion.p>

          <motion.p
            className="text-gray-400 mt-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 1.2 }}
          >
            {correctCount} of {questions.length} questions answered correctly
          </motion.p>
        </div>

        {/* Achievement Pills */}
        {achievements.length > 0 && (
          <motion.div
            className="flex flex-wrap justify-center gap-3 mt-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 1.4 }}
          >
            {achievements.map((achievement, i) => (
              <motion.div
                key={i}
                className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-full text-cyan-400 text-sm font-semibold"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3, delay: 1.6 + i * 0.1 }}
              >
                {achievement}
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* Retake Button */}
        <motion.button
          onClick={onRetake}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="mt-8 px-8 py-3 bg-cyan-600 text-white rounded-lg font-medium hover:bg-cyan-500 shadow-lg shadow-cyan-500/30 transition-all"
          style={{ fontFamily: 'Space Grotesk, sans-serif' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.8 }}
        >
          ↻ Retake Quiz
        </motion.button>
      </div>

    </motion.div>
  );
}
