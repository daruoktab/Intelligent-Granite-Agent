## 2024-12-05 13:54:38,687
**ERROR**: Error in should_use_tools: 'dict' object has no attribute 'message'


## 2024-12-05 14:02:39,316
**DEBUG**: Tool detection result: math


## 2024-12-05 14:02:39,316
**DEBUG**: Sending prompt with tools: what is 8 power by 4?


## 2024-12-05 14:02:39,730
**DEBUG**: Tool response: role='assistant' content='' images=None tool_calls=[ToolCall(function=Function(name='evaluate_expression', arguments={'expression': '8^4'}))]


## 2024-12-05 14:02:39,730
**DEBUG**: Processing tool calls: [ToolCall(function=Function(name='evaluate_expression', arguments={'expression': '8^4'}))]


## 2024-12-05 14:02:39,730
**DEBUG**: Processing tool: evaluate_expression


## 2024-12-05 14:02:39,730
**DEBUG**: Tool arguments: {'expression': '8^4'}


## 2024-12-05 14:02:39,730
**DEBUG**: Tool execution result: 4096.0


## 2024-12-05 14:02:39,730
**DEBUG**: Final results: [4096.0]


## 2024-12-05 14:04:13,901
**DEBUG**: Tool detection result: date


## 2024-12-05 14:04:13,901
**DEBUG**: Sending prompt with tools: how many days between 2002-10-10 until now?


## 2024-12-05 14:04:14,429
**DEBUG**: Tool response: role='assistant' content='' images=None tool_calls=[ToolCall(function=Function(name='date_difference', arguments={'date1': '2002-10-10', 'date2': 'today'}))]


## 2024-12-05 14:04:14,429
**DEBUG**: Processing tool calls: [ToolCall(function=Function(name='date_difference', arguments={'date1': '2002-10-10', 'date2': 'today'}))]


## 2024-12-05 14:04:14,429
**DEBUG**: Processing tool: date_difference


## 2024-12-05 14:04:14,429
**DEBUG**: Tool arguments: {'date1': '2002-10-10', 'date2': 'today'}


## 2024-12-05 14:04:14,431
**DEBUG**: Tool execution result: 8092


## 2024-12-05 14:04:14,431
**DEBUG**: Final results: [8092]


## 2024-12-05 14:10:36,391
**DEBUG**: Tool detection result: none


## 2025-04-24 08:48:04,706
**INFO**: ChatManager initialized with model: llama3.2


## 2025-04-24 08:48:04,707
**INFO**: Starting chat application


## 2025-04-24 08:49:54,908
**DEBUG**: Tool detection result: math


## 2025-04-24 08:49:54,908
**DEBUG**: Sending prompt with tools: Calculate 15% of 200


## 2025-04-24 08:49:55,453
**DEBUG**: Tool response: role='assistant' content='' images=None tool_calls=[ToolCall(function=Function(name='evaluate_expression', arguments={'expression': '0.15 * 200'}))]


## 2025-04-24 08:49:55,453
**DEBUG**: Processing tool calls: [ToolCall(function=Function(name='evaluate_expression', arguments={'expression': '0.15 * 200'}))]


## 2025-04-24 08:49:55,453
**DEBUG**: Processing tool: evaluate_expression


## 2025-04-24 08:49:55,453
**DEBUG**: Tool arguments: {'expression': '0.15 * 200'}


## 2025-04-24 08:49:55,455
**DEBUG**: Tool execution result: 30.0


## 2025-04-24 08:49:55,455
**DEBUG**: Final results: [30.0]


