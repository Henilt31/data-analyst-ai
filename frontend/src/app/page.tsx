import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-3xl w-full bg-white rounded-xl shadow-lg p-8 text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">DataMind</h1>
        <p className="text-xl text-gray-600 mb-8">
          Local-First Autonomous Exploratory Data Analysis Platform
        </p>
        <Link 
          href="/datasets" 
          className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
        >
          Go to Datasets
        </Link>
      </div>
    </div>
  );
}
