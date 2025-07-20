import React, { useState, useEffect, useRef } from 'react';
import { TypewriterPhrase } from '../../types/homepage';

interface TypewriterPreviewProps {
  phrases: TypewriterPhrase[];
  typingSpeed?: number;
  deletingSpeed?: number;
  delayBetweenPhrases?: number;
}

const TypewriterPreview: React.FC<TypewriterPreviewProps> = ({
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

  // Filter only active phrases and sort by display order
  const activePhrases = phrases
    .filter(phrase => phrase.is_active)
    .sort((a, b) => a.display_order - b.display_order);

  useEffect(() => {
    // Clean up any existing timeout
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    // If no active phrases, don't do anything
    if (activePhrases.length === 0) return;

    const currentPhrase = activePhrases[currentPhraseIndex]?.text || '';

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
            (prevIndex + 1) % activePhrases.length
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
  }, [currentText, isDeleting, isWaiting, currentPhraseIndex, activePhrases, typingSpeed, deletingSpeed, delayBetweenPhrases]);

  if (activePhrases.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">Nenhuma frase ativa para exibir</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-gray-50 rounded-lg border border-gray-200">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Renum AI</h2>
        <div className="h-16 flex items-center justify-center">
          <p className="text-xl text-gray-700">
            {currentText}
            <span className="animate-pulse">|</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default TypewriterPreview;