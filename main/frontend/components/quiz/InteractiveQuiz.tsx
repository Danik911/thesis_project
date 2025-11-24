'use client';

import { useState, useMemo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { quizQuestions } from './quizData';
import QuizCard from './QuizCard';
import QuizResults from './QuizResults';

export default function InteractiveQuiz() {
  const [retakeKey, setRetakeKey] = useState(0);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showResults, setShowResults] = useState(false);

  // Randomly select 10 questions from the pool of 20
  const selectedQuestions = useMemo(() => {
    const shuffled = [...quizQuestions].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, 10);
  }, [retakeKey]);

  const [userAnswers, setUserAnswers] = useState<(number | null)[]>(
    new Array(10).fill(null)
  );

  const handleSelectAnswer = (answerIndex: number) => {
    setSelectedAnswer(answerIndex);
  };

  const handleNext = () => {
    // Save the selected answer
    const newAnswers = [...userAnswers];
    newAnswers[currentQuestion] = selectedAnswer;
    setUserAnswers(newAnswers);

    // Check if this was the last question
    if (currentQuestion === selectedQuestions.length - 1) {
      setShowResults(true);
    } else {
      // Move to next question
      setCurrentQuestion(currentQuestion + 1);
      setSelectedAnswer(null);
    }
  };

  const handleRetake = () => {
    setRetakeKey((prev) => prev + 1); // Triggers new random selection
    setCurrentQuestion(0);
    setUserAnswers(new Array(10).fill(null));
    setSelectedAnswer(null);
    setShowResults(false);
  };

  if (showResults) {
    return (
      <QuizResults
        questions={selectedQuestions}
        userAnswers={userAnswers}
        onRetake={handleRetake}
      />
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Quiz Header - Diagonal Accent Design */}
      <div className="relative px-8 py-12 mb-8 overflow-hidden bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl">
        {/* Diagonal accent stripe */}
        <div className="absolute top-0 right-0 w-1/4 h-full bg-gradient-to-bl from-cyan-500/20 to-transparent transform rotate-12 origin-top-right" />

        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.43, 0.13, 0.23, 0.96] }}
          className="relative z-10"
        >
          <div className="flex items-center gap-3 mb-4">
            {/* SVG Badge Icon (not emoji) */}
            <svg className="w-8 h-8 text-cyan-400" viewBox="0 0 24 24" fill="none">
              <path
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className="text-cyan-400 text-sm font-semibold uppercase tracking-wider">
              Compliance Quiz
            </span>
          </div>

          <h2
            className="font-display text-5xl font-bold text-white leading-tight mb-6"
            style={{ fontFamily: 'Space Grotesk, sans-serif' }}
          >
            Validation
            <br />
            Intelligence Test
          </h2>

          {/* Progress pills - showing 10 questions */}
          <div className="flex gap-2">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-1 w-12 bg-slate-700 rounded-full" />
            ))}
          </div>
        </motion.div>
      </div>

      {/* Quiz Card with Animation */}
      <AnimatePresence mode="wait">
        <QuizCard
          key={currentQuestion}
          question={selectedQuestions[currentQuestion]}
          currentQuestion={currentQuestion + 1}
          totalQuestions={selectedQuestions.length}
          selectedAnswer={selectedAnswer}
          onSelectAnswer={handleSelectAnswer}
          onNext={handleNext}
        />
      </AnimatePresence>
    </div>
  );
}
