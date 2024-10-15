// components/ExecuteModel.js
import React, { useState } from 'react';

const ExecuteModel = ({ isOpen, onClose, token, executeTrade }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-96">
        <h3 className="text-xl text-white mb-4">Execute Trade for {token}</h3>
        <p className="text-gray-400 mb-6">
          Are you sure you want to execute the arbitrage trade for {token}?
        </p>
        <div className="flex justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Cancel
          </button>
          <button
            onClick={() => executeTrade(token)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExecuteModel;
