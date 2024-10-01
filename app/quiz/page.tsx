"use client";
import axios from 'axios';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Choice {
    choice: string;
    explanation: string;
}

interface Question {
    query: string;
    choices: Choice[];
    answer: number;
}

interface QuizData {
    questions: Question[];
}

interface QuizResponse {
    questionIndex: number;
    question: string;
    selectedChoice: number;
    availableChoices: string[];
    viewTimestamp: string;
    answerTimestamp: string;
}

interface TimestampData {
    viewTimestamp: string;
    answerTimestamp: string | null;
}

const QuizPage: React.FC = () => {
    const router = useRouter();
    const [quizData, setQuizData] = useState<QuizData | null>(null);
    const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: number }>({});
    const [showResults, setShowResults] = useState<boolean>(false);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);
    const [timestamps, setTimestamps] = useState<{ [key: number]: TimestampData }>({});

    useEffect(() => {
        // Fetch quiz data from API
        axios.get('/api/quiz/get')
            .then(response => {
                setQuizData(JSON.parse(response.data));
            })
            .catch(error => {
                console.error("Error fetching quiz data:", error);
            });

        // Load saved responses and timestamps from local storage
        const savedResponses = localStorage.getItem('quizResponses');
        const savedTimestamps = localStorage.getItem('quizTimestamps');
        if (savedResponses) {
            setSelectedAnswers(JSON.parse(savedResponses));
        }
        if (savedTimestamps) {
            setTimestamps(JSON.parse(savedTimestamps));
        }
    }, []);

    useEffect(() => {
        // Record view timestamp when changing questions
        if (quizData) {
            setTimestamps(prevTimestamps => {
                const newTimestamps = { ...prevTimestamps };
                if (!newTimestamps[currentQuestionIndex]) {
                    newTimestamps[currentQuestionIndex] = {
                        viewTimestamp: new Date().toISOString(),
                        answerTimestamp: null
                    };
                }
                localStorage.setItem('quizTimestamps', JSON.stringify(newTimestamps));
                return newTimestamps;
            });
        }
    }, [currentQuestionIndex, quizData]);

    const handleChoiceSelect = (questionIndex: number, choiceIndex: number) => {
        const newSelectedAnswers = {
            ...selectedAnswers,
            [questionIndex]: choiceIndex
        };
        setSelectedAnswers(newSelectedAnswers);

        // Update answer timestamp
        setTimestamps(prevTimestamps => {
            const newTimestamps = { ...prevTimestamps };
            if (newTimestamps[questionIndex]) {
                newTimestamps[questionIndex].answerTimestamp = new Date().toISOString();
            }
            localStorage.setItem('quizTimestamps', JSON.stringify(newTimestamps));
            return newTimestamps;
        });

        // Save to local storage
        localStorage.setItem('quizResponses', JSON.stringify(newSelectedAnswers));
    };

    const handleSubmit = async () => {
        setShowResults(true);

        if (quizData) {
            const quizResponses: QuizResponse[] = Object.entries(selectedAnswers).map(([index, choice]) => {
                const questionIndex = parseInt(index);
                const timestampData = timestamps[questionIndex] || { viewTimestamp: '', answerTimestamp: null };
                return {
                    questionIndex: questionIndex,
                    question: quizData.questions[questionIndex].query,
                    selectedChoice: choice,
                    rightChoice: quizData.questions[questionIndex].answer,
                    correctness: quizData.questions[questionIndex].answer === choice,
                    availableChoices: quizData.questions[questionIndex].choices.map(c => c.choice),
                    viewTimestamp: timestampData.viewTimestamp,
                    answerTimestamp: timestampData.answerTimestamp || new Date().toISOString()
                };
            });

            // Send quiz responses to the API
            try {
                await axios.post('/api/quiz/answer', JSON.stringify(quizResponses), {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                console.log('Quiz responses submitted successfully');
                // Clear local storage after successful submission
                localStorage.removeItem('quizResponses');
                localStorage.removeItem('quizTimestamps');

                // Redirect to /activities page
                router.push('/activities');
            } catch (error) {
                console.error('Error submitting quiz responses:', error);
            }
        }
    };

    if (!quizData) {
        return <div>Loading...</div>;
    }

    return (
        <main className="bg-black text-white min-h-screen flex">
            <div className="w-1/4 bg-gray-900 p-4">
                <h2 className="text-xl mb-4">Questions</h2>
                <ul>
                    {quizData.questions.map((_, index) => (
                        <li key={index} className="mb-2">
                            <button
                                className={`py-2 px-4 rounded-lg w-full ${currentQuestionIndex === index ? 'bg-green-400 text-black' : 'bg-gray-700 text-white'}`}
                                onClick={() => setCurrentQuestionIndex(index)}
                            >
                                Question {index + 1}
                            </button>
                        </li>
                    ))}
                </ul>
            </div>
            <div className="w-3/4 p-10">
                <div className="bg-gradient-radial from-green-400 via-transparent to-transparent rounded-lg shadow-lg p-10">
                    <h2 className="text-2xl mb-4">{quizData.questions[currentQuestionIndex].query}</h2>
                    {quizData.questions[currentQuestionIndex].choices.map((choice, choiceIndex) => (
                        <div key={choiceIndex} className="mb-2">
                            <label className="inline-flex items-center">
                                <input
                                    type="radio"
                                    name={`question-${currentQuestionIndex}`}
                                    className="form-radio text-green-400"
                                    checked={selectedAnswers[currentQuestionIndex] === choiceIndex}
                                    onChange={() => handleChoiceSelect(currentQuestionIndex, choiceIndex)}
                                />
                                <span className="ml-2">{choice.choice}</span>
                            </label>
                            {showResults && selectedAnswers[currentQuestionIndex] === choiceIndex && (
                                <p className={`text-sm mt-1 ${quizData.questions[currentQuestionIndex].answer === choiceIndex ? 'text-green-400' : 'text-red-400'}`}>
                                    {choice.explanation}
                                </p>
                            )}
                        </div>
                    ))}
                </div>
                <button
                    onClick={handleSubmit}
                    className="bg-green-400 text-black py-2 px-4 rounded-lg mt-4 hover:bg-green-500"
                >
                    Submit
                </button>
            </div>
        </main>
    );
};

export default QuizPage;