"use client";
import axios from 'axios';
import React, { useState, useEffect } from 'react';

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

const QuizPage: React.FC = () => {
    const [quizData, setQuizData] = useState<QuizData | null>(null);
    const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: number }>({});
    const [showResults, setShowResults] = useState<boolean>(false);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);

    useEffect(() => {
        // Fetch quiz data from API
        axios.get('/api/quiz/get')
            .then(response => {
                console.log(response.data)
                setQuizData(response.data);
            })
            .catch(error => {
                console.error("Error fetching quiz data:", error);
            });
    }, []);

    const handleChoiceSelect = (questionIndex: number, choiceIndex: number) => {
        setSelectedAnswers({
            ...selectedAnswers,
            [questionIndex]: choiceIndex
        });
    };

    const handleSubmit = () => {
        setShowResults(true);
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
