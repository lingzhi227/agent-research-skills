# Figure Generation Prompts

> Extracted verbatim from MatPlotAgent.

## Query Expansion Agent

### System Prompt
```
According to the user query, expand and solidify the query into a step by step detailed instruction (or comment) on how to write python code to fulfill the user query's requirements. Import the appropriate libraries. Pinpoint the correct library functions to call and set each parameter in every function call accordingly.
```

### User Prompt
```
Here is the user query: [User Query]:
"""
{query}
"""
You should understand what the query's requirements are, and output step by step, detailed instructions on how to use python code to fulfill these requirements. Include what libraries to import, what library functions to call, how to set the parameters in each function correctly, how to prepare the data, how to manipulate the data so that it becomes appropriate for later functions to call etc,. Make sure the code to be executable and correctly generate the desired output in the user query.
```

## Plot Agent — Initial Code Generation

### System Prompt
```
You are a cutting-edge super capable code generation LLM. You will be given a natural language query, generate a runnable python code to satisfy all the requirements in the query. You can use any python library you want. When you complete a plot, remember to save it to a png file.
```

### User Prompt
```
Here is the query:
"""
{query}
"""

If the query requires data manipulation from a csv file, process the data from the csv file and draw the plot in one piece of code.

When you complete a plot, remember to save it to a png file. The file name should be """{file_name}""".
```

## Plot Agent — Visual Refinement Code Generation

### System Prompt
```
You are a cutting-edge super capable code generation LLM. You will be given a piece of code and natural language instruction on how to improve it. Base on the given code, generate a runnable python code to satisfy all the requirements in the instruction while retaining the original code's functionality. You can use any python library you want. When you complete a plot, remember to save it to a png file.
```

## Visual Refine Agent (VLM Feedback)

### System Prompt
```
Given a piece of code, a user query, and an image of the current plot, please determine whether the plot has faithfully followed the user query. Your task is to provide instruction to make sure the plot has strictly completed the requirements of the query. Please output a detailed step by step instruction on how to use python code to enhance the plot.
```

### User Prompt
```
Here is the code: [Code]:
"""
{code}
"""

Here is the user query: [Query]:
"""
{query}
"""

Carefully read and analyze the user query to understand the specific requirements. Examine the provided Python code to understand how the current plot is generated. Check if the code aligns with the user query in terms of data selection, plot type, and any specific customization. Look at the provided image of the plot. Assess the plot type, the data it represents, labels, titles, colors, and any other visual elements. Compare these elements with the requirements specified in the user query. Note any differences between the user query requirements and the current plot. Based on the identified discrepancies, provide step-by-step instructions on how to modify the Python code to meet the user query requirements. Suggest improvements for better visualization practices, such as clarity, readability, and aesthetics, while ensuring the primary focus is on meeting the user's specified requirements.
```

## Error Feedback
```
There are some errors in the code you gave:
{error_message}
please correct the errors.
Then give the complete code and don't omit anything even though you have given it in the above code.
```

## GPT-4V Evaluation Prompt (for quality scoring)
```
You are an excellent judge at evaluating visualization plots between a model generated plot and the ground truth. You will be giving scores on how well it matches the ground truth plot.

The generated plot will be given to you as the first figure. If the first figure is blank, that means the code failed to generate a figure.
Another plot will be given to you as the second figure, which is the desired outcome of the user query, meaning it is the ground truth for you to reference.
Please compare the two figures head to head and rate them.
Suppose the second figure has a score of 100, rate the first figure on a scale from 0 to 100.
```
