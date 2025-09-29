# file_inserter.py - Updated to fetch files from specific folder
import mysql.connector
import os
import glob
import docx
import PyPDF2
import io

# Configuration
FILES_FOLDER = r"C:\Users\dwayn\Desktop\New folder\files"

def insert_files():
    # Database connection configuration
    db_config = {
        "host": "localhost",
        "user": "root",        # Change this if needed
        "password": "",        # Change this if needed
        "database": "mycorpus"   # Change this if needed
    }

    print("=" * 60)
    print("ISIZULU CORPUS FILE INSERTER")
    print("=" * 60)
    print(f"📁 Source folder: {FILES_FOLDER}")
    print("Supported file types: .txt, .docx, .pdf")
    
    # Check if folder exists
    if not os.path.exists(FILES_FOLDER):
        print(f"❌ Error: Folder does not exist: {FILES_FOLDER}")
        print("Please create the folder or update the FILES_FOLDER path in the script.")
        return
    
    # Get all supported files from the specified folder
    supported_files = get_supported_files()
    
    if not supported_files:
        print(f"❌ No supported files found in: {FILES_FOLDER}")
        print("Supported formats: .txt, .docx, .pdf")
        return
    
    print(f"\n📁 Found {len(supported_files)} supported file(s):")
    for i, file_info in enumerate(supported_files, 1):
        file_size = os.path.getsize(file_info['filepath'])
        print(f"  {i}. {file_info['filename']} ({file_info['type']}, {file_size} bytes)")
    
    # Process files interactively
    process_files_interactively(supported_files, db_config)

def get_supported_files():
    """Get all supported files from the specified folder"""
    supported_files = []
    
    # Check if folder exists
    if not os.path.exists(FILES_FOLDER):
        return supported_files
    
    # Text files
    text_pattern = os.path.join(FILES_FOLDER, "*.txt")
    text_files = glob.glob(text_pattern)
    for file_path in text_files:
        supported_files.append({
            'filename': os.path.basename(file_path),
            'filepath': file_path,
            'type': 'text',
            'extension': '.txt'
        })
    
    # Word documents
    docx_pattern = os.path.join(FILES_FOLDER, "*.docx")
    docx_files = glob.glob(docx_pattern)
    for file_path in docx_files:
        supported_files.append({
            'filename': os.path.basename(file_path),
            'filepath': file_path,
            'type': 'word',
            'extension': '.docx'
        })
    
    # PDF files
    pdf_pattern = os.path.join(FILES_FOLDER, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    for file_path in pdf_files:
        supported_files.append({
            'filename': os.path.basename(file_path),
            'filepath': file_path,
            'type': 'pdf',
            'extension': '.pdf'
        })
    
    return supported_files

def read_file_content(file_info):
    """Read content from different file types"""
    filepath = file_info['filepath']
    file_type = file_info['type']
    
    try:
        if file_type == 'text':
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
        
        elif file_type == 'word':
            doc = docx.Document(filepath)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        elif file_type == 'pdf':
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
                return content
        
    except Exception as e:
        print(f"❌ Error reading {file_info['filename']}: {e}")
        return None

def process_files_interactively(files, db_config):
    """Process files with interactive user input"""
    print("\n" + "=" * 60)
    print("FILE PROCESSING MODE")
    print("=" * 60)
    print("Choose processing mode:")
    print("1. Process all files automatically")
    print("2. Process files interactively (ask for each file)")
    print("3. Skip processing")
    
    try:
        mode_choice = input("\nEnter your choice (1-3): ").strip()
        
        if mode_choice == '3':
            print("⏭️  Skipping file processing.")
            return
        elif mode_choice == '1':
            print("🤖 Processing all files automatically...")
            process_files_automatically(files, db_config)
        elif mode_choice == '2':
            print("💬 Processing files interactively...")
            process_files_one_by_one(files, db_config)
        else:
            print("❌ Invalid choice. Using interactive mode.")
            process_files_one_by_one(files, db_config)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Process interrupted by user.")
        return
    except Exception as e:
        print(f"❌ Error: {e}")

def process_files_one_by_one(files, db_config):
    """Process each file one by one with user input"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("✅ Connected to the database")

        processed_count = 0
        skipped_count = 0
        
        for file_info in files:
            print(f"\n" + "=" * 50)
            print(f"PROCESSING: {file_info['filename']}")
            print("=" * 50)
            
            # Read file content
            print("📖 Reading file content...")
            content = read_file_content(file_info)
            
            if content is None:
                print("❌ Failed to read file content. Skipping...")
                skipped_count += 1
                continue
            
            # Show preview of content
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"📄 Content preview: {preview}")
            print(f"📊 File size: {len(content)} characters")
            
            # Ask user if they want to process this file
            while True:
                process_file = input("\nProcess this file? (y/n/skip): ").strip().lower()
                if process_file in ['y', 'yes', 'n', 'no', 'skip']:
                    break
                print("❌ Please enter 'y', 'n', or 'skip'")
            
            if process_file in ['n', 'no']:
                print("⏭️  Skipping this file.")
                skipped_count += 1
                continue
            elif process_file == 'skip':
                print("⏭️  Skipping remaining files.")
                break
            
            # Get file details from user
            title = get_user_input("Enter document title: ", 
                                  default=os.path.splitext(file_info['filename'])[0])
            
            genre = get_genre_choice()
            
            source = get_user_input("Enter document source: ", 
                                   default="File Upload")
            
            # Confirm details
            print(f"\n📋 Document Details:")
            print(f"   Title: {title}")
            print(f"   Genre: {genre}")
            print(f"   Source: {source}")
            print(f"   File: {file_info['filename']}")
            print(f"   Path: {file_info['filepath']}")
            
            confirm = input("\nConfirm and insert into database? (y/n): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("⏭️  Skipping this file.")
                skipped_count += 1
                continue
            
            # Insert into database
            if insert_document(cursor, conn, title, content, genre, source):
                processed_count += 1
                print("✅ Document inserted successfully!")
            else:
                skipped_count += 1
        
        print(f"\n📊 Processing complete: {processed_count} inserted, {skipped_count} skipped")
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("🔌 Database connection closed")

def process_files_automatically(files, db_config):
    """Process all files automatically with auto-detection"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("✅ Connected to the database")

        processed_count = 0
        skipped_count = 0
        
        for file_info in files:
            try:
                print(f"\n🔍 Processing: {file_info['filename']}")
                
                # Read file content
                content = read_file_content(file_info)
                if content is None:
                    print("❌ Failed to read file content. Skipping...")
                    skipped_count += 1
                    continue
                
                # Extract filename without extension for title
                title = os.path.splitext(file_info['filename'])[0]
                
                # Check if this document already exists
                check_query = "SELECT id FROM documents WHERE title = %s"
                cursor.execute(check_query, (title,))
                existing_doc = cursor.fetchone()
                
                if existing_doc:
                    print(f"⏭️  Skipping '{title}' - already exists (ID: {existing_doc[0]})")
                    skipped_count += 1
                    continue
                
                # Determine genre automatically
                genre = determine_genre(title, content)
                source = "Automated Import"
                
                # Insert the document
                if insert_document(cursor, conn, title, content, genre, source):
                    processed_count += 1
                    print(f"✅ Auto-inserted: {title} (Genre: {genre})")
                else:
                    skipped_count += 1
                
            except Exception as e:
                print(f"❌ Error processing {file_info['filename']}: {e}")
                skipped_count += 1
                continue

        print(f"\n📊 Processing complete: {processed_count} inserted, {skipped_count} skipped")
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("🔌 Database connection closed")

def get_user_input(prompt, default=""):
    """Get user input with optional default value"""
    if default:
        prompt += f" [{default}]: "
    else:
        prompt += ": "
    
    user_input = input(prompt).strip()
    return user_input if user_input else default

def get_genre_choice():
    """Get genre choice from user"""
    genres = {
        '1': 'news',
        '2': 'literature', 
        '3': 'conversation',
        '4': 'other'
    }
    
    print("\n📚 Choose genre:")
    print("1. News (Izindaba)")
    print("2. Literature (Izincwadi)")
    print("3. Conversation (Izingxoxo)")
    print("4. Other (Okunye)")
    
    while True:
        choice = input("Enter choice (1-4): ").strip()
        if choice in genres:
            return genres[choice]
        print("❌ Invalid choice. Please enter 1-4")

def insert_document(cursor, conn, title, content, genre, source):
    """Insert document into database"""
    try:
        # Check if document with same title already exists
        check_query = "SELECT id FROM documents WHERE title = %s"
        cursor.execute(check_query, (title,))
        if cursor.fetchone():
            print(f"❌ Document with title '{title}' already exists")
            return False
        
        # Insert new document
        insert_query = """
        INSERT INTO documents (title, text, genre, source)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (title, content, genre, source))
        conn.commit()
        
        # Get the ID of the inserted document
        cursor.execute("SELECT LAST_INSERT_ID()")
        doc_id = cursor.fetchone()[0]
        print(f"📄 Inserted document ID: {doc_id}")
        
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Error inserting document: {e}")
        conn.rollback()
        return False

def determine_genre(title, content):
    """Determine the genre based on filename or content analysis"""
    title_lower = title.lower()
    content_lower = content.lower()
    
    # Simple genre detection based on keywords
    news_keywords = ['news', 'izindaba', 'sports', 'game', 'umdlalo', 'goal', 'team', 'soccer', 'football', 'match']
    literature_keywords = ['book', 'incwadi', 'story', 'literature', 'umlando', 'tale', 'folklore', 'chapter', 'novel']
    conversation_keywords = ['conversation', 'ingxoxo', 'dialogue', 'chat', 'sawubona', 'yebo', 'hamba kahle', 'hello', 'greeting']
    
    # Check title first
    if any(word in title_lower for word in news_keywords):
        return 'news'
    elif any(word in title_lower for word in literature_keywords):
        return 'literature'
    elif any(word in title_lower for word in conversation_keywords):
        return 'conversation'
    
    # Then check content if title doesn't help
    word_count = {}
    for word in content_lower.split():
        clean_word = word.strip('.,!?;:"\'()')
        if len(clean_word) > 3:  # Only consider words longer than 3 characters
            word_count[clean_word] = word_count.get(clean_word, 0) + 1
    
    # Check for genre keywords in content
    news_score = sum(word_count.get(word, 0) for word in news_keywords)
    literature_score = sum(word_count.get(word, 0) for word in literature_keywords)
    conversation_score = sum(word_count.get(word, 0) for word in conversation_keywords)
    
    scores = {
        'news': news_score,
        'literature': literature_score, 
        'conversation': conversation_score
    }
    
    # Return genre with highest score, or 'other' if no clear match
    best_genre = max(scores, key=scores.get)
    return best_genre if scores[best_genre] > 2 else 'other'

def show_statistics(db_config):
    """Show current database statistics"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) as total FROM documents")
        total_docs = cursor.fetchone()["total"]
        
        cursor.execute("SELECT genre, COUNT(*) as count FROM documents GROUP BY genre")
        genre_stats = cursor.fetchall()
        
        print(f"\n📊 CURRENT CORPUS STATISTICS:")
        print(f"   Total documents: {total_docs}")
        for stat in genre_stats:
            print(f"   {stat['genre']}: {stat['count']}")
            
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def check_folder_contents():
    """Check what's in the folder"""
    print(f"\n🔍 Checking folder contents: {FILES_FOLDER}")
    
    if not os.path.exists(FILES_FOLDER):
        print("❌ Folder does not exist!")
        return
    
    all_files = os.listdir(FILES_FOLDER)
    if not all_files:
        print("📁 Folder is empty")
        return
    
    print(f"📁 Total files in folder: {len(all_files)}")
    for file in all_files:
        file_path = os.path.join(FILES_FOLDER, file)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            print(f"   {file} ({size} bytes)")

if __name__ == "__main__":
    # Show folder contents first
    check_folder_contents()
    
    # Show current statistics
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "", 
        "database": "mycorpus"
    }
    
    show_statistics(db_config)
    
    # Start file insertion process
    insert_files()
    
    # Show final statistics
    print("\n" + "=" * 60)
    show_statistics(db_config)
    print("=" * 60)
    print("🎉 File insertion process completed!")