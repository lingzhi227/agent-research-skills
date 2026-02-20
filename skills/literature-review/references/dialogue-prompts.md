# Literature Review Dialogue Prompts Reference

Extracted from STORM (Stanford).

## 1. Persona Generation

### Find Related Topics
```
I'm writing a Wikipedia page for a topic mentioned below. Please identify and recommend some Wikipedia pages on closely related subjects. I'm looking for examples that provide insights into interesting aspects commonly associated with this topic, or examples that help me understand the typical content and structure included in Wikipedia pages for similar topics.
Please list the urls in separate lines.
```

### Generate Expert Personas
```
You need to select a group of Wikipedia editors who will work together to create a comprehensive article on the topic. Each of them represents a different perspective, role, or affiliation related to this topic. You can use other Wikipedia pages of related topics for inspiration. For each editor, add a description of what they will focus on.
Give your answer in the following format: 1. short summary of editor 1: description\n2. short summary of editor 2: description\n...
```

### Generate Focused Experts
```
You need to select a group of speakers who will be suitable to have roundtable discussion on the [topic] of specific [focus].
You may consider inviting speakers having opposite stands on the topic; speakers representing different interest parties.
Ensure that the selected speakers are directly connected to the specific context and scenario provided.
For each speaker, add a description of their interests and what they will focus on during the discussion.
Strictly follow format below:
1. [speaker 1 role]: [speaker 1 short description]
2. [speaker 2 role]: [speaker 2 short description]
```

## 2. Multi-Turn Q&A Dialogue

### Ask Question (basic)
```
You are an experienced Wikipedia writer. You are chatting with an expert to get information for the topic you want to contribute. Ask good questions to get more useful information relevant to the topic.
When you have no more question to ask, say "Thank you so much for your help!" to end the conversation.
Please only ask a question at a time and don't ask what you have asked before. Your questions should be related to the topic you want to write.
```

### Ask Question with Persona
```
You are an experienced Wikipedia writer and want to edit a specific page. Besides your identity as a Wikipedia writer, you have specific focus when researching the topic.
Now, you are chatting with an expert to get information. Ask good questions to get more useful information.
When you have no more question to ask, say "Thank you so much for your help!" to end the conversation.
Please only ask a question at a time and don't ask what you have asked before. Your questions should be related to the topic you want to write.
```

### Convert Question to Search Queries
```
You want to answer the question using Google search. What do you type in the search box?
Write the queries you will use in the following format:
- query 1
- query 2
...
- query n
```

### Answer Question (grounded in search results)
```
You are an expert who can use information effectively. You are chatting with a Wikipedia writer who wants to write a Wikipedia page on topic you know. You have gathered the related information and will now use the information to form a response.
Make your response as informative as possible, ensuring that every sentence is supported by the gathered information. If the [gathered information] is not directly related to the [topic] or [question], provide the most relevant answer based on the available information. If no appropriate answer can be formulated, respond with, "I cannot answer this question based on the available information," and explain any limitations or gaps.
```

## 3. Grounded Discussion Focus

```
Your job is to find next discussion focus in a roundtable conversation. You will be given previous conversation summary and some information that might assist you discover new discussion focus.
Note that the new discussion focus should bring new angle and perspective to the discussion and avoid repetition. The new discussion focus should be grounded on the available information and push the boundaries of the current discussion for broader exploration.
The new discussion focus should have natural flow from last utterance in the conversation.
Use [1][2] in line to ground your question.
```

## 4. Outline Generation

### Initial Outline
```
Write an outline for a Wikipedia page.
Here is the format of your writing:
1. Use "#" Title" to indicate section title, "##" Title" to indicate subsection title, "###" Title" to indicate subsubsection title, and so on.
2. Do not include other information.
3. Do not include topic name itself in the outline.
```

### Outline Refinement from Conversations
```
Improve an outline for a Wikipedia page. You already have a draft outline that covers the general information. Now you want to improve it based on the information learned from an information-seeking conversation to make it more informative.
Here is the format of your writing:
1. Use "#" Title" to indicate section title, "##" Title" to indicate subsection title, "###" Title" to indicate subsubsection title, and so on.
2. Do not include other information.
3. Do not include topic name itself in the outline.
```

## 5. Core Code Pattern: Conversation Simulator

```python
class ConvSimulator:
    def forward(self, topic, persona, ground_truth_url, callback_handler):
        dlg_history = []
        for _ in range(self.max_turn):
            # Persona asks question
            user_utterance = self.wiki_writer(
                topic=topic, persona=persona, dialogue_turns=dlg_history
            ).question

            # Check termination
            if "Thank you so much for your help!" in user_utterance:
                break

            # Expert answers with grounded information
            expert_output = self.topic_expert(
                topic=topic, question=user_utterance,
                ground_truth_url=ground_truth_url
            )

            dlg_turn = DialogueTurn(
                agent_utterance=expert_output.answer,
                user_utterance=user_utterance,
                search_queries=expert_output.queries,
                search_results=expert_output.searched_results,
            )
            dlg_history.append(dlg_turn)
```

## 6. Concurrent Persona Execution

```python
def _run_conversation(self, conv_simulator, topic, considered_personas):
    conversations = []
    max_workers = min(self.max_thread_num, len(considered_personas))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_persona = {
            executor.submit(conv_simulator, topic, persona, ...): persona
            for persona in considered_personas
        }
        for future in as_completed(future_to_persona):
            persona = future_to_persona[future]
            conv = future.result()
            conversations.append((persona, conv.dlg_history))

    return conversations
```

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| max_turn | 3-5 | Dialogue turns per persona |
| num_personas | 3-5 | Number of expert perspectives |
| max_search_queries | 3 | Queries per question |
| word_limit | 1000 | Max words per expert answer |
| max_thread_num | 5 | Concurrent persona threads |
