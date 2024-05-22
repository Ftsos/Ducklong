"use client";
import axios from 'axios';
import React, { useEffect, useState } from 'react';
import Button from '../components/button';
import { useRouter } from 'next/navigation';

const fileLoadingPage = () => {

    const [files, setFiles]:any = useState({});
    const [selectedScript, setSelectedScript] = useState<string | null>(null); // State to hold selected script
    const [selectedTranscript, setSelectedTranscript] = useState<string | null>(null); // State to hold selected transcript
    const router = useRouter(); // Initialize useRouter


    useEffect(() => {
        axios.get('/api/getFiles').then((res: any) => setFiles(res.data)).catch(err => console.log(err))
    }, [])
    

    const handleScriptClick = (file: string) => {
        setSelectedScript(file === selectedScript ? null : file);
    };

    // Handle click on transcript file
    const handleTranscriptClick = (file: string) => {
        setSelectedTranscript(file === selectedTranscript ? null : file);
    };

    const handleSendButtonClick = () => {
        // Check if any file is selected
        if (selectedScript || selectedTranscript) {
            console.log({ script: selectedScript, transcript: selectedTranscript })
            // If a file is selected, send POST request to /api/setFile
            axios.post('/api/setFile', { script: selectedScript, transcription: selectedTranscript })
                .then((response) => {
                    // If successful, navigate to another page
                    router.push('/activities');; // Specify the URL of the other page
                })
                .catch((error) => {
                    console.error('Error sending files:', error);
                });
        } else {
            // If no file is selected, show an alert or perform any other action
            alert('Please select at least one file.');
        }
    };

    return (
        <main>
            <div className="flex justify-center items-center h-screen">
                <div className="bg-gradient-radial from-green-400 via-transparent to-transparent rounded-lg shadow-lg p-20">
                    <h1 className="text-4xl font-bold text-center text-purple-600 mb-8">
                        Load Files
                    </h1>
                    <div className="flex justify-between mb-8">
                        <div className="w-1/2 mr-4">
                            <div className="bg-gray-800 rounded-lg shadow-md p-4 max-h-96 overflow-y-auto">
                                <h2 className="text-2xl font-bold mb-4 text-center text-white">Scripts</h2>

                                <div className="bg-gray-700 rounded-md p-4">

                                    {files && files.scripts && files.scripts.length > 0 ? (
                                            files.scripts.map((file: any) => (
                                                <div
                                                    key={file}
                                                    className={`text-lg font-semibold text-gray-300 p-1 rounded cursor-pointer ${selectedScript === file ? 'bg-purple-500 text-white' : ''
                                                        }`}
                                                    onClick={() => handleScriptClick(file)}
                                                    onMouseEnter={(e) => e.currentTarget.classList.add('bg-gray-600')}
                                                    onMouseLeave={(e) => e.currentTarget.classList.remove('bg-gray-600')}
                                                >
                                                    <span className='m-2'>{file}</span>
                                                </div>
                                            ))) : (
                                        <p className="text-lg font-semibold text-gray-300">No scripts found.</p>
                                    )
                                    }

                                  
                                </div>
                            </div>
                        </div>
                        <div className="w-1/2 ml-4">
                            <div className="bg-gray-800 rounded-lg shadow-md p-4 max-h-96 overflow-y-auto">
                                <h2 className="text-2xl font-bold mb-4 text-center text-white">Transcripts</h2>

                                <div className="bg-gray-700 rounded-md p-4">
                                    {files && files.transcripts && files.transcripts.length > 0 ? (
                                        files.transcripts.map((file: any) => (
                                            <div
                                                key={file}
                                                className={`text-lg font-semibold text-gray-300 p-1 rounded cursor-pointer ${selectedTranscript === file ? 'bg-purple-500 text-white' : ''
                                                    }`}
                                                onClick={() => handleTranscriptClick(file)}
                                                onMouseEnter={(e) => e.currentTarget.classList.add('bg-gray-600')}
                                                onMouseLeave={(e) => e.currentTarget.classList.remove('bg-gray-600')}
                                            >
                                                <span className='m-2'>{file}</span>
                                            </div>
                                        ))) : (
                                        <p className="text-lg font-semibold text-gray-300">No Transcripts found.</p>
                                    )
                                    }

                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="flex justify-center">
                        <Button onClick={handleSendButtonClick} className={'hover:bg-green-700 transition duration-300'}>Send</Button>
                    </div>
                </div>
            </div>
        </main>
    );
};

export default fileLoadingPage;