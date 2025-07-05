// "use client";
// import React from 'react';

// interface Platform {
//   id: string;
//   name: string;
//   icon: string;
// }

// interface PlatformTabsProps {
//   platforms: Platform[];
//   activeTab: string;
//   onTabChange: (platformId: string) => void;
// }

// const PlatformTabs: React.FC<PlatformTabsProps> = ({ platforms, activeTab, onTabChange }) => {
//   return (
//     <div className="mb-6 flex flex-wrap gap-2 rounded-lg border border-stroke bg-white p-1.5 shadow-default dark:border-stroke dark:border-strokedark dark:bg-boxdark">
//       {platforms.map((platform) => (
//         <button
//           key={platform.id}
//           onClick={() => onTabChange(platform.id)}
//           className={`flex items-center gap-2.5 rounded-md px-4 py-2.5 text-sm font-medium transition-all duration-300 ${
//             activeTab === platform.id
//               ? 'bg-primary text-white shadow-card'
//               : 'text-body hover:bg-gray-2 hover:text-black dark:text-bodydark dark:hover:bg-meta-4 dark:hover:text-white'
//           }`}
//         >
//           <span className="text-base">{platform.icon}</span>
//           {platform.name}
//         </button>
//       ))}
//     </div>
//   );
// };

// export default PlatformTabs;