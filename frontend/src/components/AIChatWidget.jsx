import React, { useState, useRef, useEffect } from 'react'
import { useAI } from '@/hooks/useAI'

function AIChatWidget() {
  const { loading, chatWithAI } = useAI()
  const [isExpanded, setIsExpanded] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hello! I'm your AI security assistant. Ask me anything about vulnerabilities, patches, or security best practices." }
  ])
  const [userInput, setUserInput] = useState('')
  const messagesContainerRef = useRef(null)

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const toggleExpand = () => {
    setIsExpanded(!isExpanded)
  }

  const sendMessage = async () => {
    if (!userInput.trim() || loading) return

    const newMessages = [...messages, { role: 'user', content: userInput }]
    setMessages(newMessages)

    const query = userInput
    setUserInput('')

    const response = await chatWithAI(query, newMessages.slice(0, -1))

    if (response) {
      setMessages(prev => [...prev, { role: 'assistant', content: response }])
    } else {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }])
    }
  }

  const handleKeyUp = (e) => {
    if (e.key === 'Enter') sendMessage()
  }

  return (
    <div className={`ai-chat-widget ${isExpanded ? 'expanded' : ''}`}>
      <div className="chat-header" onClick={toggleExpand}>
        <span>🤖 AI Security Assistant</span>
        <button className="toggle-btn">{isExpanded ? '−' : '+'}</button>
      </div>

      {isExpanded && (
        <div className="chat-body">
          <div className="messages" ref={messagesContainerRef}>
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-content">{msg.content}</div>
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <div className="message-content typing">AI is thinking...</div>
              </div>
            )}
          </div>

          <div className="chat-input">
            <input
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyUp={handleKeyUp}
              placeholder="Ask about vulnerabilities, patches, or security..."
              disabled={loading}
            />
            <button onClick={sendMessage} disabled={loading || !userInput}>
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default AIChatWidget
