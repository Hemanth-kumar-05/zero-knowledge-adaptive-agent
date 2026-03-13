# Data Structures and Algorithms - Course Syllabus

**Course Code:** CS2301  
**Credits:** 4  
**Contact Hours:** 3L + 1T (Lecture + Tutorial)  
**Prerequisites:** Programming Fundamentals (CS1101)

---

## Course Objectives

1. Understand fundamental data structures and their operations
2. Analyze time and space complexity of algorithms
3. Design and implement efficient algorithms for real-world problems
4. Apply appropriate data structures to solve computational problems
5. Evaluate trade-offs between different data structure implementations

---

## Course Outcomes (CO)

| CO | Description | Bloom's Level |
|----|-------------|---------------|
| CO1 | Understand and explain various data structures including arrays, linked lists, stacks, queues, trees, and graphs | L2 (Understand) |
| CO2 | Analyze the time and space complexity of algorithms using Big-O notation | L4 (Analyze) |
| CO3 | Implement and apply appropriate data structures to solve computational problems | L3 (Apply) |
| CO4 | Design efficient algorithms using advanced data structures | L5 (Evaluate) |
| CO5 | Compare and evaluate different data structure implementations for specific use cases | L5 (Evaluate) |

---

## Module 1: Introduction to Data Structures (8 hours)

### Topics Covered:
- Basic concepts of data structures
- Abstract Data Types (ADT)
- Algorithm analysis fundamentals
- Time and space complexity
- Asymptotic notation (Big-O, Big-Omega, Big-Theta)
- Best case, average case, and worst case analysis

### Learning Outcomes:
- CO1: Understand the concept of ADT and data structure classification
- CO2: Analyze algorithm complexity using asymptotic notation

### Bloom's Taxonomy Mapping:
- L1 (Remember): Define data structures, list types of complexity
- L2 (Understand): Explain time complexity, describe asymptotic notation
- L3 (Apply): Calculate Big-O notation for simple algorithms
- L4 (Analyze): Compare different complexity classes

---

## Module 2: Linear Data Structures (10 hours)

### Topics Covered:
- **Arrays**: Static and dynamic arrays, multi-dimensional arrays
- **Linked Lists**: Singly linked lists, doubly linked lists, circular linked lists
- **Stacks**: Array-based and linked list-based implementation, applications (expression evaluation, parenthesis matching, tower of Hanoi)
- **Queues**: Linear queue, circular queue, priority queue, double-ended queue (deque)
- **Applications**: Infix to postfix conversion, recursion implementation

### Learning Outcomes:
- CO1: Understand various linear data structures and their properties
- CO3: Implement stacks and queues using arrays and linked lists
- CO2: Analyze performance of different implementations

### Bloom's Taxonomy Mapping:
- L2 (Understand): Explain stack LIFO and queue FIFO principles
- L3 (Apply): Implement linked list operations (insert, delete, search)
- L4 (Analyze): Compare array-based vs linked list-based implementations
- L5 (Evaluate): Choose appropriate data structure for given problem

---

## Module 3: Trees (12 hours)

### Topics Covered:
- **Tree Fundamentals**: Tree terminology, binary trees, tree traversals (inorder, preorder, postorder, level-order)
- **Binary Search Trees (BST)**: Properties, insertion, deletion, search operations
- **Performance Analysis**: Time complexity of BST operations (O(log n) average, O(n) worst case)
- **Balanced Trees**: 
  - **AVL Trees**: Balance factor, rotations (LL, RR, LR, RL), insertion and deletion
  - **Red-Black Trees**: Properties, color scheme, rotations, applications
  - **B-Trees**: Structure, insertion, deletion, applications in databases
- **Tree Applications**: Expression trees, Huffman coding, file systems

### Key Concepts:
- **BST Property**: For every node, left subtree values < node value < right subtree values
- **AVL Balance Factor**: Height difference between left and right subtrees must be ≤ 1
- **Red-Black Properties**: Root is black, red nodes have black children, all paths have same black height
- **Time Complexity**: 
  - BST (balanced): O(log n) for search, insert, delete
  - BST (unbalanced): O(n) worst case
  - AVL trees: O(log n) guaranteed for all operations
  - Red-Black trees: O(log n) with less frequent rotations than AVL

### Learning Outcomes:
- CO1: Understand tree structures and their variations
- CO3: Implement BST operations and tree traversals
- CO4: Design self-balancing tree structures
- CO2: Analyze time complexity of tree operations

### Bloom's Taxonomy Mapping:
- L2 (Understand): Explain BST properties and AVL balance factor
- L3 (Apply): Implement tree traversal algorithms and BST operations
- L4 (Analyze): Compare BST, AVL, and Red-Black trees performance
- L5 (Evaluate): Decide when to use balanced vs unbalanced trees
- L6 (Create): Design new tree-based solutions for custom requirements

---

## Module 4: Hashing (6 hours)

### Topics Covered:
- Hash functions and hash tables
- Collision resolution: Chaining, open addressing (linear probing, quadratic probing, double hashing)
- Load factor and rehashing
- Applications: Database indexing, caching, symbol tables
- Time complexity: O(1) average case for insert, search, delete

### Learning Outcomes:
- CO3: Implement hash tables with collision handling
- CO4: Design efficient hash functions for specific data types
- CO5: Evaluate trade-offs between different collision resolution strategies

### Bloom's Taxonomy Mapping:
- L3 (Apply): Implement hash table operations
- L4 (Analyze): Analyze collision rates for different hash functions
- L5 (Evaluate): Compare chaining vs open addressing methods

---

## Module 5: Graphs (10 hours)

### Topics Covered:
- Graph terminology: Vertices, edges, degree, path, cycle
- Graph representations: Adjacency matrix, adjacency list
- Graph traversals: Breadth-First Search (BFS), Depth-First Search (DFS)
- **Shortest Path Algorithms**:
  - Dijkstra's algorithm (single source, non-negative weights)
  - Bellman-Ford algorithm (single source, negative weights allowed)
  - Floyd-Warshall algorithm (all pairs shortest path)
- **Minimum Spanning Tree**:
  - Prim's algorithm
  - Kruskal's algorithm
- Applications: Social networks, route planning, network design

### Learning Outcomes:
- CO3: Implement graph traversal algorithms
- CO4: Design solutions using shortest path and MST algorithms
- CO2: Analyze time complexity of graph algorithms

### Bloom's Taxonomy Mapping:
- L2 (Understand): Explain graph representations and properties
- L3 (Apply): Implement BFS and DFS traversals
- L4 (Analyze): Compare Dijkstra's vs Bellman-Ford algorithms
- L5 (Evaluate): Select appropriate algorithm for graph problems

---

## Module 6: Advanced Topics (8 hours)

### Topics Covered:
- **Heaps**: Min-heap, max-heap, heap operations, heap sort, priority queues
- **Tries**: Prefix trees, insertion, search, applications in autocomplete
- **Disjoint Sets**: Union-Find data structure with path compression
- **Skip Lists**: Probabilistic data structure for fast search

### Learning Outcomes:
- CO3: Implement heap and trie data structures
- CO5: Evaluate advanced data structures for specialized applications

### Bloom's Taxonomy Mapping:
- L3 (Apply): Implement heap operations and heapify
- L4 (Analyze): Analyze heap sort time complexity
- L5 (Evaluate): Compare tries vs hash tables for string storage

---

## Assessment Pattern

| Component | Weightage | CO Mapping |
|-----------|-----------|------------|
| Continuous Assessment 1 (CA1) | 15% | CO1, CO2 |
| Continuous Assessment 2 (CA2) | 15% | CO3, CO4 |
| Assignments | 10% | CO3, CO5 |
| Lab Evaluation | 10% | CO3 |
| End Semester Exam (ESE) | 50% | CO1-CO5 |

---

## End Semester Exam Pattern

**Total Marks:** 60  
**Duration:** 3 hours

### Section A: Multiple Choice Questions (10 marks)
- 5 questions × 2 marks each
- Coverage: All modules
- Bloom's levels: L1-L3
- CO mapping: CO1, CO2, CO3

### Section B: Short Answer Questions (15 marks)
- 3 questions × 5 marks each
- Coverage: All modules
- Bloom's levels: L2-L4
- CO mapping: CO2, CO3, CO4

### Section C: Long Answer Questions (35 marks)
- Part 1: 2 questions × 10 marks = 20 marks (Compulsory)
- Part 2: 1 question × 15 marks = 15 marks (Choice of 1 from 2)
- Coverage: Emphasis on Module 3, 5, 6
- Bloom's levels: L4-L6
- CO mapping: CO3, CO4, CO5

### Question Distribution Guidelines:
- **Module 1**: 10% weightage (foundational concepts)
- **Module 2**: 15% weightage (linear structures)
- **Module 3**: 25% weightage (trees - major focus)
- **Module 4**: 10% weightage (hashing)
- **Module 5**: 25% weightage (graphs)
- **Module 6**: 15% weightage (advanced topics)

### Difficulty Distribution:
- Easy (L1-L2): 25%
- Medium (L3-L4): 50%
- Hard (L5-L6): 25%

---

## Recommended Questions for Module 3 (Trees)

### Easy Level (L2 - Understand):
1. Explain the properties of a Binary Search Tree with an example
2. Define the balance factor in AVL trees
3. What is the time complexity of search operation in a balanced BST?
4. Describe the four types of rotations in AVL trees
5. List the properties of Red-Black trees

### Medium Level (L3-L4 - Apply/Analyze):
1. Implement the insertion algorithm for a Binary Search Tree
2. Given a sequence of insertions, construct the resulting AVL tree showing all rotations
3. Compare the time complexities of BST, AVL, and Red-Black trees for search, insert, and delete operations
4. Analyze the worst-case scenario for an unbalanced BST and suggest a solution
5. Apply inorder, preorder, and postorder traversals on a given binary tree

### Hard Level (L5-L6 - Evaluate/Create):
1. Design a self-balancing binary search tree variant optimized for read-heavy workloads
2. Critically evaluate when to use AVL trees vs Red-Black trees in a database index
3. Create an algorithm to detect if a binary tree is a valid BST
4. Propose a data structure combining BST and heap properties and justify its applications
5. Develop a strategy to convert an unbalanced BST into a balanced AVL tree with minimum rotations

---

## Reference Books

1. **Textbook**: "Data Structures and Algorithms in Java" by Michael T. Goodrich, Roberto Tamassia
2. "Introduction to Algorithms" by Cormen, Leiserson, Rivest, and Stein (CLRS)
3. "Data Structures Using C" by Reema Thareja
4. "Algorithm Design Manual" by Steven Skiena
5. Online Resources: GeeksforGeeks, LeetCode, HackerRank

---

## Lab Components

Students must complete minimum 12 lab exercises covering:
- Linked list implementations
- Stack and queue applications
- Binary tree traversals
- BST operations with balancing
- Graph traversal algorithms
- Sorting algorithms comparison

---

**Last Updated:** January 2026  
**Course Coordinator:** Dr. Sarah Thompson  
**Department:** Computer Science & Engineering  
**Institution:** Nova Crest Institute of Engineering
