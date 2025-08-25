import React, { useState } from 'react';

const FollowUpInput: React.FC = () => {
  const [question, setQuestion] = useState('');

  const handleQuestionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuestion(e.target.value);
  };

  const handleSubmit = () => {
    if (question.trim()) {
      // Logic to handle the follow-up question will be implemented here.
      // For now, it will just log to the console.
      console.log('Follow-up question:', question);
      alert(`Your question has been submitted: "${question}"`);
      setQuestion('');
    }
  };

  return (
    <div className="follow-up-section">
      <h3>Have a follow-up question?</h3>
      <div className="input-group">
        <input
          type="text"
          value={question}
          onChange={handleQuestionChange}
          placeholder="Ask about the perspectives or summary..."
        />
        <button onClick={handleSubmit}>Ask</button>
      </div>
    </div>
  );
};

export default FollowUpInput;
