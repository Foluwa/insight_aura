"use client";
import React, { useState, useEffect } from 'react';
import { Platform, SearchFormData, AnalysisProgress } from '@/types/sentiment';
interface SearchPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onAnalysisComplete: (data: SearchFormData & { platform: string }) => void;
}

const platforms: Platform[] = [
  {
    id: 'appstore',
    name: 'App Store',
    icon: '🍎',
    searchPlaceholder: 'Enter app name or App Store ID...',
    examples: [
      { text: 'Instagram', value: 'Instagram' },
      { text: 'WhatsApp', value: 'WhatsApp Messenger' },
      { text: 'Spotify', value: 'Spotify: Music and Podcasts' }
    ]
  },
  {
    id: 'playstore',
    name: 'Google Play',
    icon: '🤖',
    searchPlaceholder: 'Enter app name or package name...',
    examples: [
      { text: 'Instagram', value: 'Instagram' },
      { text: 'com.instagram.android', value: 'com.instagram.android' },
      { text: 'com.whatsapp', value: 'com.whatsapp' }
    ]
  },
  {
    id: 'youtube',
    name: 'YouTube',
    icon: '📺',
    searchPlaceholder: 'Paste YouTube video URL...',
    examples: [
      { text: 'https://youtube.com/watch?v=...', value: 'https://youtube.com/watch?v=dQw4w9WgXcQ' },
      { text: 'https://youtu.be/...', value: 'https://youtu.be/dQw4w9WgXcQ' }
    ]
  }
];

const SearchPanel: React.FC<SearchPanelProps> = ({ isOpen, onClose, onAnalysisComplete }) => {
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null);
  const [formData, setFormData] = useState<SearchFormData>({
    searchTerm: '',
    includeRecentReviews: true,
    enableAiInsights: true,
    includeCompetitorComparison: false
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<AnalysisProgress>({
    step: 0,
    totalSteps: 4,
    currentStep: '',
    completed: []
  });

  const handlePlatformSelect = (platform: Platform) => {
    setSelectedPlatform(platform);
    setFormData(prev => ({ ...prev, searchTerm: '' }));
  };

  const handleInputChange = (field: keyof SearchFormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const fillExample = (value: string) => {
    setFormData(prev => ({ ...prev, searchTerm: value }));
  };

  const startAnalysis = async () => {
    if (!formData.searchTerm.trim() || !selectedPlatform) return;

    setIsAnalyzing(true);
    const steps = ['Fetching data', 'Processing reviews', 'Generating insights', 'Creating visualizations'];
    
    for (let i = 0; i < steps.length; i++) {
      setAnalysisProgress({
        step: i + 1,
        totalSteps: steps.length,
        currentStep: steps[i],
        completed: steps.slice(0, i)
      });
      
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    setTimeout(() => {
      onAnalysisComplete({
        ...formData,
        platform: selectedPlatform.name
      });
      resetForm();
      onClose();
    }, 1000);
  };

  const resetForm = () => {
    setSelectedPlatform(null);
    setFormData({
      searchTerm: '',
      includeRecentReviews: true,
      enableAiInsights: true,
      includeCompetitorComparison: false
    });
    setIsAnalyzing(false);
    setAnalysisProgress({
      step: 0,
      totalSteps: 4,
      currentStep: '',
      completed: []
    });
  };

  useEffect(() => {
    if (!isOpen) {
      resetForm();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-99999 flex items-center justify-center bg-black/80 backdrop-blur-sm px-4 py-5">
      <div className="w-full max-w-142.5 max-h-full overflow-y-auto rounded-[10px] bg-white shadow-1 dark:bg-gray-dark dark:shadow-card">
        <div className="border-b border-stroke px-7.5 py-4 dark:border-dark-3">
          <div className="flex items-center justify-between">
            <h3 className="text-body-2xlg font-bold text-dark dark:text-white">
              Start New Analysis
            </h3>
            <button
              onClick={onClose}
              className="flex h-7 w-7 items-center justify-center rounded-lg hover:bg-gray-2 dark:hover:bg-dark-3"
            >
              <svg
                className="fill-current"
                width="18"
                height="18"
                viewBox="0 0 18 18"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M13.7535 2.47502H11.5879V1.9969C11.5879 1.15315 10.9129 0.478149 10.0691 0.478149H7.90352C7.05977 0.478149 6.38477 1.15315 6.38477 1.9969V2.47502H4.21914C3.40352 2.47502 2.72852 3.15002 2.72852 3.96565V4.8094C2.72852 5.42815 3.09414 5.9344 3.62852 6.1594L4.07852 15.4688C4.13477 16.6219 5.09102 17.5219 6.24414 17.5219H11.7004C12.8535 17.5219 13.8098 16.6219 13.866 15.4688L14.3441 6.13127C14.8785 5.90627 15.2441 5.3719 15.2441 4.78127V3.93752C15.2441 3.15002 14.5691 2.47502 13.7535 2.47502ZM7.67852 1.9969C7.67852 1.85627 7.79102 1.74377 7.93164 1.74377H10.0973C10.2379 1.74377 10.3504 1.85627 10.3504 1.9969V2.47502H7.70664V1.9969H7.67852ZM4.02227 3.96565C4.02227 3.85315 4.10664 3.74065 4.24727 3.74065H13.7535C13.866 3.74065 13.9785 3.82502 13.9785 3.96565V4.8094C13.9785 4.9219 13.8941 5.0344 13.7535 5.0344H4.24727C4.13477 5.0344 4.02227 4.95002 4.02227 4.8094V3.96565ZM11.7285 16.2563H6.27227C5.79414 16.2563 5.40039 15.8906 5.37227 15.3844L4.95039 6.2719H13.0785L12.6566 15.3844C12.6004 15.8625 12.2066 16.2563 11.7285 16.2563Z"
                  fill=""
                />
                <path
                  d="M9.00039 9.11255C8.66289 9.11255 8.35352 9.3938 8.35352 9.75942V13.3313C8.35352 13.6688 8.63477 13.9782 9.00039 13.9782C9.33789 13.9782 9.64727 13.6969 9.64727 13.3313V9.75942C9.64727 9.3938 9.33789 9.11255 9.00039 9.11255Z"
                  fill=""
                />
                <path
                  d="M11.2502 9.67504C10.8846 9.64692 10.6033 9.90004 10.5752 10.2657L10.4064 12.7407C10.3783 13.0782 10.6314 13.3875 10.9971 13.4157C11.0252 13.4157 11.0252 13.4157 11.0533 13.4157C11.3908 13.4157 11.6721 13.1625 11.6721 12.825L11.8408 10.35C11.8408 9.98442 11.5877 9.70317 11.2502 9.67504Z"
                  fill=""
                />
                <path
                  d="M6.72245 9.67504C6.38495 9.70317 6.1037 10.0125 6.13182 10.35L6.3287 12.825C6.35683 13.1625 6.63808 13.4157 6.94745 13.4157C6.97558 13.4157 6.97558 13.4157 7.0037 13.4157C7.34120 13.3875 7.62245 13.0782 7.59433 12.7407L7.39745 10.2657C7.39745 9.90004 7.08808 9.64692 6.72245 9.67504Z"
                  fill=""
                />
              </svg>
            </button>
          </div>
        </div>

        <div className="p-7.5">
          {!isAnalyzing ? (
            <>
              {/* Platform Selection */}
              {!selectedPlatform && (
                <div className="mb-6 grid grid-cols-3 gap-4">
                  {platforms.map((platform) => (
                    <div
                      key={platform.id}
                      onClick={() => handlePlatformSelect(platform)}
                      className="cursor-pointer rounded-[10px] bg-white p-6 text-center shadow-1 hover:shadow-2 dark:bg-gray-dark dark:shadow-card"
                    >
                      <div className="mb-3 text-4xl">{platform.icon}</div>
                      <h4 className="mb-2 text-lg font-bold text-dark dark:text-white">{platform.name}</h4>
                      <p className="text-sm text-dark dark:text-dark-6">Search by app name or ID</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Search Form */}
              {selectedPlatform && (
                <div className="space-y-6">
                  <div>
                    <label className="mb-3 block text-body-sm font-medium text-dark dark:text-white">
                      {selectedPlatform.name} Search
                    </label>
                    <div className="flex gap-3">
                      <input
                        type="text"
                        value={formData.searchTerm}
                        onChange={(e) => handleInputChange('searchTerm', e.target.value)}
                        placeholder={selectedPlatform.searchPlaceholder}
                        className="w-full rounded-[7px] border-[1.5px] border-stroke bg-transparent px-5.5 py-3 text-dark outline-none transition focus:border-primary active:border-primary disabled:cursor-default disabled:bg-gray dark:border-dark-3 dark:bg-dark-2 dark:text-white dark:focus:border-primary"
                      />
                      <button
                        onClick={startAnalysis}
                        disabled={!formData.searchTerm.trim()}
                        className="inline-flex items-center justify-center rounded-[7px] bg-primary px-6 py-3 text-center font-medium text-white hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition duration-300"
                      >
                        Analyze
                      </button>
                    </div>
                  </div>

                  {/* Examples */}
                  <div>
                    <p className="mb-3 text-body-sm text-dark dark:text-dark-6">Examples:</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedPlatform.examples.map((example, index) => (
                        <button
                          key={index}
                          onClick={() => fillExample(example.value)}
                          className="rounded-full border border-stroke bg-gray-2 px-4 py-2 text-body-sm text-dark transition-all duration-300 hover:bg-primary hover:text-white dark:border-dark-3 dark:bg-dark-2 dark:text-white dark:hover:bg-primary"
                        >
                          {example.text}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Options */}
                  <div className="space-y-4 border-t border-stroke pt-6 dark:border-dark-3">
                    {[
                      { key: 'includeRecentReviews', label: 'Include recent reviews (last 30 days)' },
                      { key: 'enableAiInsights', label: 'Enable AI insights' },
                      { key: 'includeCompetitorComparison', label: 'Include competitor comparison' }
                    ].map((option) => (
                      <label key={option.key} className="flex cursor-pointer select-none items-center">
                        <div className="relative">
                          <input
                            type="checkbox"
                            checked={formData[option.key as keyof SearchFormData] as boolean}
                            onChange={(e) => handleInputChange(option.key as keyof SearchFormData, e.target.checked)}
                            className="sr-only"
                          />
                          <div className={`mr-4 flex h-5 w-5 items-center justify-center rounded border ${
                            formData[option.key as keyof SearchFormData] 
                              ? 'border-primary bg-gray dark:bg-transparent' 
                              : 'border-stroke dark:border-dark-3'
                          }`}>
                            <span className={`opacity-0 ${formData[option.key as keyof SearchFormData] ? '!opacity-100' : ''}`}>
                              <svg width="11" height="8" viewBox="0 0 11 8" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="m10.0915 0.951972-5.87253 6.033424-2.606514-2.677L1.607424 4.316l.982132 1.017L7.47736 5.958L10.0915.951972Z" fill="#3C50E0" stroke="#3C50E0" strokeWidth="0.25"/>
                              </svg>
                            </span>
                          </div>
                        </div>
                        <p className="text-dark dark:text-white">{option.label}</p>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Analysis Progress */
            <div className="py-8 text-center">
              <div className="mb-6 text-6xl animate-pulse">⚡</div>
              <h4 className="mb-3 text-body-2xlg font-bold text-dark dark:text-white">Analysis in Progress</h4>
              <p className="mb-8 text-dark dark:text-dark-6">We're analyzing sentiment data across multiple sources...</p>
              
              <div className="mb-8 h-2 w-full rounded-full bg-stroke dark:bg-dark-3">
                <div 
                  className="h-2 rounded-full bg-primary transition-all duration-500"
                  style={{ width: `${(analysisProgress.step / analysisProgress.totalSteps) * 100}%` }}
                />
              </div>

              <div className="space-y-3 text-left">
                {['Fetching data', 'Processing reviews', 'Generating insights', 'Creating visualizations'].map((step, index) => (
                  <div key={index} className="flex items-center gap-3 rounded-[7px] bg-gray-2 p-3 dark:bg-dark-2">
                    <div className={`flex h-6 w-6 items-center justify-center rounded-full text-body-sm text-white ${
                      index < analysisProgress.step ? 'bg-green-light-1' :
                      index === analysisProgress.step ? 'bg-primary animate-pulse' :
                      'bg-dark-5'
                    }`}>
                      {index < analysisProgress.step ? '✓' : index === analysisProgress.step ? '🔄' : '⏳'}
                    </div>
                    <span className={`${
                      index < analysisProgress.step ? 'text-green-light-1' :
                      index === analysisProgress.step ? 'text-primary' :
                      'text-dark dark:text-dark-6'
                    }`}>
                      {step}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchPanel;