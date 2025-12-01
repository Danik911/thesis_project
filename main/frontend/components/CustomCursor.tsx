import { useEffect, useState, useCallback, useRef } from 'react'

interface CursorState {
  x: number
  y: number
  isHovering: boolean
  isHidden: boolean
}

export default function CustomCursor() {
  const [cursor, setCursor] = useState<CursorState>({
    x: 0,
    y: 0,
    isHovering: false,
    isHidden: true,
  })
  const [isVisible, setIsVisible] = useState(false)
  const ringRef = useRef<HTMLDivElement>(null)
  const dotRef = useRef<HTMLDivElement>(null)

  // Check if device supports hover (not touch-only)
  const isTouchDevice = useCallback(() => {
    if (typeof window === 'undefined') return true
    return window.matchMedia('(pointer: coarse)').matches
  }, [])

  // Check reduced motion preference
  const prefersReducedMotion = useCallback(() => {
    if (typeof window === 'undefined') return false
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  }, [])

  useEffect(() => {
    // Don't show custom cursor on touch devices or if reduced motion is preferred
    if (isTouchDevice() || prefersReducedMotion()) {
      return
    }

    setIsVisible(true)
    document.body.classList.add('custom-cursor-active')

    const handleMouseMove = (e: MouseEvent) => {
      // Update dot position immediately
      if (dotRef.current) {
        dotRef.current.style.transform = `translate3d(${e.clientX}px, ${e.clientY}px, 0)`
      }

      // Ring follows with slight delay via CSS transition
      if (ringRef.current) {
        ringRef.current.style.transform = `translate3d(${e.clientX}px, ${e.clientY}px, 0)`
      }

      setCursor((prev) => ({
        ...prev,
        x: e.clientX,
        y: e.clientY,
        isHidden: false,
      }))
    }

    const handleMouseEnter = () => {
      setCursor((prev) => ({ ...prev, isHidden: false }))
    }

    const handleMouseLeave = () => {
      setCursor((prev) => ({ ...prev, isHidden: true }))
    }

    const handleElementHover = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      const isInteractive =
        target.closest('a, button, [role="button"], .btn-primary, .btn-secondary, [data-cursor="expand"]') !== null

      setCursor((prev) => ({ ...prev, isHovering: isInteractive }))
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseenter', handleMouseEnter)
    document.addEventListener('mouseleave', handleMouseLeave)
    document.addEventListener('mouseover', handleElementHover)

    return () => {
      document.body.classList.remove('custom-cursor-active')
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseenter', handleMouseEnter)
      document.removeEventListener('mouseleave', handleMouseLeave)
      document.removeEventListener('mouseover', handleElementHover)
    }
  }, [isTouchDevice, prefersReducedMotion])

  if (!isVisible) return null

  return (
    <>
      {/* Outer ring - follows with slight delay */}
      <div
        ref={ringRef}
        className={`
          fixed pointer-events-none z-[9999]
          -translate-x-1/2 -translate-y-1/2
          rounded-full
          border-2 border-cyan-400/60
          transition-all duration-150 ease-out
          will-change-transform
          ${cursor.isHovering ? 'w-14 h-14 border-blue-400/80' : 'w-10 h-10'}
          ${cursor.isHidden ? 'opacity-0 scale-0' : 'opacity-100 scale-100'}
        `}
        style={{
          boxShadow: cursor.isHovering
            ? '0 0 20px rgba(59, 130, 246, 0.5), 0 0 40px rgba(6, 182, 212, 0.3)'
            : '0 0 10px rgba(6, 182, 212, 0.3)',
          left: 0,
          top: 0,
        }}
      />

      {/* Inner dot - follows immediately */}
      <div
        ref={dotRef}
        className={`
          fixed pointer-events-none z-[9999]
          -translate-x-1/2 -translate-y-1/2
          rounded-full
          bg-gradient-to-br from-blue-400 to-cyan-400
          transition-opacity duration-100
          will-change-transform
          ${cursor.isHovering ? 'w-4 h-4' : 'w-3 h-3'}
          ${cursor.isHidden ? 'opacity-0' : 'opacity-100'}
        `}
        style={{
          boxShadow: '0 0 8px rgba(59, 130, 246, 0.8), 0 0 16px rgba(6, 182, 212, 0.5)',
          left: 0,
          top: 0,
        }}
      />
    </>
  )
}
