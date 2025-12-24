// Framer Motion animation variants for report components
// Premium animation system for CRB Analyser

// === BASIC ANIMATIONS ===

export const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
  transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }
}

export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.4, ease: 'easeOut' }
}

export const scaleIn = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
  transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }
}

export const slideInLeft = {
  initial: { opacity: 0, x: -30 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 30 },
  transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }
}

export const slideInRight = {
  initial: { opacity: 0, x: 30 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -30 },
  transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }
}

// === STAGGER ANIMATIONS ===

export const staggerContainer = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1
    }
  }
}

export const staggerContainerFast = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.05
    }
  }
}

export const staggerItem = {
  initial: { opacity: 0, y: 15 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }
  }
}

export const staggerItemScale = {
  initial: { opacity: 0, scale: 0.9 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }
  }
}

// === EXPANDABLE SECTIONS ===

export const expandCollapse = {
  initial: { height: 0, opacity: 0 },
  animate: {
    height: 'auto',
    opacity: 1,
    transition: {
      height: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] },
      opacity: { duration: 0.3, delay: 0.1 }
    }
  },
  exit: {
    height: 0,
    opacity: 0,
    transition: {
      height: { duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] },
      opacity: { duration: 0.2 }
    }
  }
}

// === TAB ANIMATIONS ===

export const tabContent = {
  initial: { opacity: 0, y: 10 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: 'easeOut' }
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: { duration: 0.2, ease: 'easeIn' }
  }
}

export const tabIndicator = {
  layout: true,
  transition: {
    type: 'spring',
    stiffness: 500,
    damping: 35
  }
}

// === SPRING ANIMATIONS ===

export const springNumber = {
  type: 'spring',
  stiffness: 100,
  damping: 15
}

export const springBounce = {
  type: 'spring',
  stiffness: 400,
  damping: 25
}

export const springSmooth = {
  type: 'spring',
  stiffness: 200,
  damping: 30
}

// === CARD & HOVER EFFECTS ===

export const cardHover = {
  scale: 1.02,
  y: -4,
  boxShadow: '0 20px 40px -12px rgba(0, 0, 0, 0.15)',
  transition: { duration: 0.3, ease: 'easeOut' }
}

export const cardHoverSubtle = {
  scale: 1.01,
  boxShadow: '0 10px 30px -10px rgba(0, 0, 0, 0.12)',
  transition: { duration: 0.25, ease: 'easeOut' }
}

export const buttonHover = {
  scale: 1.02,
  transition: { duration: 0.2 }
}

export const buttonTap = {
  scale: 0.98
}

// === PAGE TRANSITIONS ===

export const pageTransition = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { duration: 0.4, ease: 'easeOut' }
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.3, ease: 'easeIn' }
  }
}

// === SPECIAL EFFECTS ===

export const glowPulse = {
  animate: {
    boxShadow: [
      '0 0 20px -5px rgba(147, 51, 234, 0.2)',
      '0 0 30px -5px rgba(147, 51, 234, 0.4)',
      '0 0 20px -5px rgba(147, 51, 234, 0.2)'
    ],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
}

export const floatAnimation = {
  animate: {
    y: [0, -6, 0],
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
}

// === CHART ANIMATIONS ===

export const chartReveal = {
  initial: { pathLength: 0, opacity: 0 },
  animate: {
    pathLength: 1,
    opacity: 1,
    transition: { duration: 1.5, ease: 'easeOut' }
  }
}

export const gaugeAnimation = {
  initial: { rotate: -90 },
  animate: (score: number) => ({
    rotate: -90 + (score / 100) * 180,
    transition: {
      duration: 1.5,
      ease: [0.25, 0.46, 0.45, 0.94],
      delay: 0.3
    }
  })
}

export const barGrow = {
  initial: { scaleX: 0, originX: 0 },
  animate: {
    scaleX: 1,
    transition: { duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }
  }
}

// === NUMBER COUNTER ===

export const numberReveal = {
  initial: { opacity: 0, y: 10 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' }
  }
}

// === SKELETON LOADING ===

export const shimmer = {
  animate: {
    backgroundPosition: ['200% 0', '-200% 0'],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'linear'
    }
  }
}

// === MODAL ANIMATIONS ===

export const modalBackdrop = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.2 }
}

export const modalContent = {
  initial: { opacity: 0, scale: 0.95, y: 20 },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: [0.25, 0.46, 0.45, 0.94]
    }
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 20,
    transition: { duration: 0.2 }
  }
}

// === SCROLL TRIGGERED ===

export const scrollReveal = {
  initial: { opacity: 0, y: 40 },
  whileInView: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }
  },
  viewport: { once: true, margin: '-100px' }
}

// === PREMIUM EFFECTS ===

export const premiumCardEntrance = {
  initial: { opacity: 0, y: 30, scale: 0.98 },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.6,
      ease: [0.25, 0.46, 0.45, 0.94]
    }
  }
}

export const premiumGlow = {
  animate: {
    boxShadow: [
      '0 0 30px -10px rgba(147, 51, 234, 0.15)',
      '0 0 40px -8px rgba(147, 51, 234, 0.25)',
      '0 0 30px -10px rgba(147, 51, 234, 0.15)'
    ],
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
}

export const premiumShimmer = {
  animate: {
    backgroundPosition: ['-200% 0', '200% 0'],
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: 'linear',
      repeatDelay: 2
    }
  }
}

export const pulseRing = {
  animate: {
    scale: [1, 1.1, 1],
    opacity: [0.5, 0.8, 0.5],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
}

// === HOVER EFFECTS ===

export const liftOnHover = {
  whileHover: {
    y: -4,
    boxShadow: '0 20px 40px -15px rgba(0, 0, 0, 0.12)',
    transition: { duration: 0.25, ease: 'easeOut' }
  },
  whileTap: { scale: 0.98 }
}

export const glowOnHover = {
  whileHover: {
    boxShadow: '0 0 30px -5px rgba(147, 51, 234, 0.3)',
    transition: { duration: 0.3, ease: 'easeOut' }
  }
}

export const scaleOnHover = {
  whileHover: {
    scale: 1.02,
    transition: { duration: 0.2, ease: 'easeOut' }
  },
  whileTap: { scale: 0.98 }
}

// === GRADIENT ANIMATIONS ===

export const gradientShift = {
  animate: {
    backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
    transition: {
      duration: 5,
      repeat: Infinity,
      ease: 'linear'
    }
  }
}

// === LOADING STATES ===

export const skeletonPulse = {
  animate: {
    opacity: [0.5, 1, 0.5],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
}

export const loadingDots = {
  animate: (i: number) => ({
    y: [0, -8, 0],
    transition: {
      duration: 0.6,
      repeat: Infinity,
      delay: i * 0.15,
      ease: 'easeInOut'
    }
  })
}

// === NOTIFICATION/BADGE EFFECTS ===

export const badgeBounce = {
  animate: {
    scale: [1, 1.1, 1],
    transition: {
      duration: 0.3,
      repeat: 2,
      repeatDelay: 3
    }
  }
}

export const attentionPulse = {
  animate: {
    scale: [1, 1.05, 1],
    boxShadow: [
      '0 0 0 0 rgba(147, 51, 234, 0.4)',
      '0 0 0 8px rgba(147, 51, 234, 0)',
      '0 0 0 0 rgba(147, 51, 234, 0)'
    ],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeOut'
    }
  }
}

// === ICON ANIMATIONS ===

export const iconBounce = {
  animate: {
    y: [0, -3, 0],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
}

export const iconRotate = {
  whileHover: {
    rotate: 15,
    scale: 1.1,
    transition: { duration: 0.2 }
  }
}

export const iconPop = {
  initial: { scale: 0, rotate: -180 },
  animate: {
    scale: 1,
    rotate: 0,
    transition: {
      type: 'spring',
      stiffness: 260,
      damping: 20
    }
  }
}

// === PROGRESS ANIMATIONS ===

export const progressFill = {
  initial: { width: 0 },
  animate: (percent: number) => ({
    width: `${percent}%`,
    transition: {
      duration: 1,
      ease: [0.25, 0.46, 0.45, 0.94]
    }
  })
}

export const progressPulse = {
  animate: {
    opacity: [0.7, 1, 0.7],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
}
