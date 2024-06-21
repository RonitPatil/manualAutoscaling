# Elastic Face Recognition Application Using AWS IaaS

## Overview
This project involves developing an elastic face recognition application using AWS IaaS resources. The application is designed to recognize faces in images by leveraging a multi-tier architecture and autoscaling capabilities.

## Project Description
The project is divided into three main tiers:
- **Web Tier**: Handles incoming HTTP requests from users, processes image uploads, and forwards them to the App Tier for face recognition. It also returns the recognition results to the users.
- **App Tier**: Utilizes a deep learning model to perform face recognition on the images received from the Web Tier. This tier dynamically scales based on the request load to ensure efficient processing.
- **Data Tier**: Stores input images and the corresponding recognition results in AWS S3 buckets for persistence and retrieval.

## Key Features
- **Autoscaling**: The App Tier can automatically scale in and out based on the incoming request load, ensuring optimal resource utilization and cost efficiency.
- **Face Recognition**: The application uses a pre-trained deep learning model to accurately recognize faces in uploaded images.
- **Persistence**: All input images and recognition results are stored in S3, allowing for persistent storage and future reference.

## How It Works
1. Users upload images through the Web Tier.
2. The Web Tier forwards these images to the App Tier for processing.
3. The App Tier uses the deep learning model to recognize faces in the images.
4. Recognition results are sent back to the Web Tier, which then responds to the user.
5. All images and results are stored in S3 for persistence.

This setup ensures that the application can handle varying levels of load efficiently while providing accurate face recognition results.
