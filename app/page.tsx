"use client";
import Image from 'next/image'
import Link from 'next/link'
import { useState } from 'react';
import Button from './components/button';
import axios from 'axios';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);

  const handleChooseFileButtonClick = (e: any) => {
    let input: HTMLInputElement = document.createElement("input");
    input.type = 'file';
    input.click()
    input.addEventListener('change', (e: any) => {setFile(e.target.files[0])})
  };

  const handleSendButtonClick = (e: any) => {
    if(!file) {
      //Add some error to the client later
      return;
    }
    axios.post('/api/file', 
      {
        file
      }, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      } 
    ).then(res => console.log(res)).catch(err => console.log(err))
  }

  return (
    <main>
      <div className="flex justify-center items-center h-screen">
        <div className="bg-gradient-radial from-green-400 via-transparent to-transparent rounded-lg shadow-lg p-40">
          <h1 className="text-6xl font-bold text-center text-red-600 mb-8">Ducklong</h1>          
          <h1 className="text-2xl font-bold mb-4">Upload File</h1>

          <div className="relative">
            
            <Button onClick={handleChooseFileButtonClick}>
              Choose File
            </Button>
          </div>
          {file && (
            <p className="mt-4">
              Selected file: <strong>{file.name}</strong>

              <Button className='bg-purple-500 bg-opacity-80 mt-4' onClick={handleSendButtonClick}>Send</Button>
            </p>
          )}
          <p className="mt-4">
            Or <Link href="/fileLoading">
                <b>Load a File</b>
               </Link>
          </p>

        </div>
      </div>
    </main>
  )
}
