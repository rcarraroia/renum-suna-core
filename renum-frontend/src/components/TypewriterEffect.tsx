import React, { useState, useEffect, useRef } from 'react';

interface TypewriterEffectProps {
  phrases: string[];
  typingSpeed?: number;
  deletingSpeed?: number;
  delayBetweenPhrases?: number;
}

const TypewriterEffect: React.FC<TypewriterEffectProps> = ({
  phrases,
  typingSpeed = 100,
  deletingSpeed = 50,
  delayBetweenPhrases = 2000,
}) => {
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
  const [currentText, setCurrentText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Clean up any existing timeout
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    // If no phrases, don't do anything
    if (phrases.length === 0) return;

    const currentPhrase = phrases[currentPhraseIndex] || '';

    // Handle the typewriter effect
    const handleTyping = () => {
      if (isWaiting) {
        // If waiting, move to deleting after delay
        timeoutRef.current = setTimeout(() => {
          setIsWaiting(false);
          setIsDeleting(true);
        }, delayBetweenPhrases);
      } else if (isDeleting) {
        // If deleting, remove one character at a time
        if (currentText.length > 0) {
          setCurrentText(currentText.slice(0, -1));
          timeoutRef.current = setTimeout(handleTyping, deletingSpeed);
        } else {
          // When done deleting, move to the next phrase
          setIsDeleting(false);
          setCurrentPhraseIndex((prevIndex) => 
            (prevIndex + 1) % phrases.length
          );
        }
      } else {
        // If typing, add one character at a time
        if (currentText.length < currentPhrase.length) {
          setCurrentText(currentPhrase.slice(0, currentText.length + 1));
          timeoutRef.current = setTimeout(handleTyping, typingSpeed);
        } else {
          // When done typing, wait before deleting
          setIsWaiting(true);
          timeoutRef.current = setTimeout(handleTyping, delayBetweenPhrases);
        }
      }
    };

    // Start the typing effect
    timeoutRef.current = setTimeout(handleTyping, 100);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [currentText, isDeleting, isWaiting, currentPhraseIndex, phrases, typingSpeed, deletingSpeed, delayBetweenPhrases]);

  return (
    <div className="h-16 flex items-center justify-center">
      <p className="text-xl md:text-2xl lg:text-3xl text-gray-800 font-light">
        {currentText}
        <span className="animate-pulse">|</span>
      </p>
    </div>
  );
};

export default TypewriterEffect;