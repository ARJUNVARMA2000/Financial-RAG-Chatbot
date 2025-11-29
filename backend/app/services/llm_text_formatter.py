"""
Enhanced text formatter to clean up LLM responses before displaying to user.
This version handles severely broken spacing from PDFs.
"""

import re
from typing import Optional


def format_response_text(text: str) -> str:
    """
    Clean and format text response from LLM.
    Fixes spacing issues, formatting problems, and ensures consistent display.
    
    Args:
        text: Raw text from LLM response
        
    Returns:
        Cleaned and formatted text
    """
    if not text:
        return text
    
    # AGGRESSIVE FIXES FOR BROKEN PDF TEXT
    
    # Step 1: Fix numbers followed immediately by "billion/million/trillion"
    text = re.sub(r'(\d+\.?\d*)billion', r'\1 billion', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+\.?\d*)million', r'\1 million', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+\.?\d*)trillion', r'\1 trillion', text, flags=re.IGNORECASE)
    
    # Step 2: Fix "17.4billion" -> "$17.4 billion" (add dollar sign if missing)
    text = re.sub(r'(?<!\$)(\d+\.?\d*)\s+(billion|million|trillion)', r'$\1 \2', text, flags=re.IGNORECASE)
    
    # Step 3: Fix missing spaces after periods (but not decimals)
    # This handles "billion.This" -> "billion. This"
    text = re.sub(r'([a-z])\.([A-Z])', r'\1. \2', text)
    
    # Step 4: Fix missing spaces after punctuation
    text = re.sub(r'([.!?,;:])([A-Za-z0-9])', r'\1 \2', text)
    
    # Step 5: Fix camelCase issues (lowercase followed by uppercase)
    # "Thisfigure" -> "This figure", "includesspecial" -> "includes special"
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # Step 6: Fix missing spaces after numbers followed by letters
    text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
    
    # Step 7: Fix multiple consecutive words stuck together (common patterns)
    # This is the nuclear option - split when we see lowercase->lowercase without space
    # But only for common word boundaries
    word_boundaries = [
        (r'billionrelated', 'billion related'),
        (r'billionin', 'billion in'),
        (r'billionfor', 'billion for'),
        (r'billionand', 'billion and'),
        (r'millionin', 'million in'),
        (r'millionand', 'million and'),
        (r'costswithout', 'costs without'),
        (r'costsWithout', 'costs Without'),
        (r'chargesoperating', 'charges operating'),
        (r'chargesof', 'charges of'),
        (r'incomewould', 'income would'),
        (r'incomewas', 'income was'),
        (r'wouldhave', 'would have'),
        (r'havebeen', 'have been'),
        (r'Thisfigure', 'This figure'),
        (r'figureinclude', 'figure include'),
        (r'includesspecial', 'includes special'),
        (r'includescharge', 'includes charge'),
        (r'includestwo', 'includes two'),
        (r'specialcharges', 'special charges'),
        (r'estimatedseverance', 'estimated severance'),
        (r'severancecosts', 'severance costs'),
        (r'Withoutthese', 'Without these'),
        (r'withoutthe', 'without the'),
        (r'andthe', 'and the'),
        (r'ofthe', 'of the'),
        (r'forthe', 'for the'),
        (r'inthe', 'in the'),
        (r'tothe', 'to the'),
        (r'onthe', 'on the'),
        (r'wasthe', 'was the'),
        (r'fromthe', 'from the'),
    ]
    
    for pattern, replacement in word_boundaries:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Step 8: Fix missing spaces before opening brackets/parentheses
    text = re.sub(r'([a-z0-9])(\()', r'\1 \2', text)
    text = re.sub(r'([a-z0-9])(\[)', r'\1 \2', text)
    
    # Step 9: Fix missing spaces after closing brackets/parentheses
    text = re.sub(r'(\))([A-Za-z0-9])', r'\1 \2', text)
    text = re.sub(r'(\])([A-Za-z0-9])', r'\1 \2', text)
    
    # Step 10: Fix multiple consecutive uppercase letters followed by lowercase
    # "FTCand" -> "FTC and"
    text = re.sub(r'([A-Z]{2,})([a-z])', r'\1 \2', text)
    
    # Step 11: Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Step 12: Fix weird spacing around decimals like "2. 5" -> "2.5"
    text = re.sub(r'(\d+)\.\s+(\d+)', r'\1.\2', text)
    
    # Step 12b: Fix duplicated numbers like "117.4" -> "17.4", "2.2.5" -> "2.5"
    # Pattern: digit-digit-dot-digit where first two digits are same
    text = re.sub(r'\b(\d)(\1)\.(\d+)\b', r'\1.\3', text)
    # Pattern: digit-dot-digit-dot-digit like "2.2.5" -> "2.5"
    text = re.sub(r'\b(\d)\.(\1)\.(\d+)\b', r'\1.\3', text)
    # Pattern: three-digit duplicates like "221" -> "21"
    text = re.sub(r'\b(\d)(\d)(\2)\b', r'\1\2', text)
    
    # Step 13: Clean up whitespace around newlines
    text = re.sub(r'\n +', '\n', text)
    text = re.sub(r' +\n', '\n', text)
    
    # Step 14: Normalize multiple newlines (max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Step 15: Ensure proper spacing after list markers
    text = re.sub(r'^(\d+\.|[-*•])\s*', r'\1 ', text, flags=re.MULTILINE)
    
    return text.strip()


def format_financial_numbers(text: str) -> str:
    """
    Additional formatting specifically for financial numbers and currencies.
    
    Args:
        text: Text with financial data
        
    Returns:
        Text with properly formatted financial numbers
    """
    # Ensure $ is attached to numbers (no space)
    text = re.sub(r'\$\s+(\d)', r'$\1', text)
    
    # Ensure space after billion/million/trillion
    text = re.sub(r'(\d+\.?\d*)\s*billion', r'\1 billion', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+\.?\d*)\s*million', r'\1 million', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+\.?\d*)\s*trillion', r'\1 trillion', text, flags=re.IGNORECASE)
    
    return text


def format_llm_response(raw_response: str) -> str:
    """
    Main function to format LLM response.
    Use this function to clean all responses before displaying.
    
    Args:
        raw_response: Raw text from LLM
        
    Returns:    
        Cleaned and formatted response ready for display
    """
    if not raw_response:
        return raw_response
    
    # Strip any hidden Unicode formatting characters that might affect rendering
    # Remove zero-width spaces, formatting marks, etc.
    import unicodedata
    raw_response = ''.join(char for char in raw_response 
                           if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')
        
    # Apply general text formatting
    formatted = format_response_text(raw_response)
    
    # Apply financial-specific formatting
    formatted = format_financial_numbers(formatted)
    
    return formatted



# import re
# from typing import Optional


# def format_response_text(text: str) -> str:
#     """
#     Clean and format text response from LLM.
#     Fixes spacing issues, formatting problems, and ensures consistent display.
    
#     Args:
#         text: Raw text from LLM response
        
#     Returns:
#         Cleaned and formatted text
#     """
#     if not text:
#         return text
    
#     # AGGRESSIVE FIXES FOR BROKEN PDF TEXT
    
#     # Step 1: Fix numbers followed immediately by "billion/million/trillion"
#     text = re.sub(r'(\d+\.?\d*)billion', r'\1 billion', text, flags=re.IGNORECASE)
#     text = re.sub(r'(\d+\.?\d*)million', r'\1 million', text, flags=re.IGNORECASE)
#     text = re.sub(r'(\d+\.?\d*)trillion', r'\1 trillion', text, flags=re.IGNORECASE)
    
#     # Step 2: Fix "17.4billion" -> "$17.4 billion" (add dollar sign if missing)
#     text = re.sub(r'(?<!\$)(\d+\.?\d*)\s+(billion|million|trillion)', r'$\1 \2', text, flags=re.IGNORECASE)
    
#     # Step 3: Fix missing spaces after periods (but not decimals)
#     # This handles "billion.This" -> "billion. This"
#     text = re.sub(r'([a-z])\.([A-Z])', r'\1. \2', text)
    
#     # Step 4: Fix missing spaces after punctuation
#     text = re.sub(r'([.!?,;:])([A-Za-z0-9])', r'\1 \2', text)
    
#     # Step 5: Fix camelCase issues (lowercase followed by uppercase)
#     # "Thisfigure" -> "This figure", "includesspecial" -> "includes special"
#     text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
#     # Step 6: Fix missing spaces after numbers followed by letters
#     text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
    
#     # Step 7: Fix multiple consecutive words stuck together (common patterns)
#     # This is the nuclear option - split when we see lowercase->lowercase without space
#     # But only for common word boundaries
#     word_boundaries = [
#         (r'billionrelated', 'billion related'),
#         (r'billionin', 'billion in'),
#         (r'billionfor', 'billion for'),
#         (r'billionand', 'billion and'),
#         (r'millionin', 'million in'),
#         (r'millionand', 'million and'),
#         (r'costswithout', 'costs without'),
#         (r'costsWithout', 'costs Without'),
#         (r'chargesoperating', 'charges operating'),
#         (r'chargesof', 'charges of'),
#         (r'incomewould', 'income would'),
#         (r'incomewas', 'income was'),
#         (r'wouldhave', 'would have'),
#         (r'havebeen', 'have been'),
#         (r'Thisfigure', 'This figure'),
#         (r'figureinclude', 'figure include'),
#         (r'includesspecial', 'includes special'),
#         (r'includescharge', 'includes charge'),
#         (r'includestwo', 'includes two'),
#         (r'specialcharges', 'special charges'),
#         (r'estimatedseverance', 'estimated severance'),
#         (r'severancecosts', 'severance costs'),
#         (r'Withoutthese', 'Without these'),
#         (r'withoutthe', 'without the'),
#         (r'andthe', 'and the'),
#         (r'ofthe', 'of the'),
#         (r'forthe', 'for the'),
#         (r'inthe', 'in the'),
#         (r'tothe', 'to the'),
#         (r'onthe', 'on the'),
#         (r'wasthe', 'was the'),
#         (r'fromthe', 'from the'),
#     ]
    
#     for pattern, replacement in word_boundaries:
#         text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
#     # Step 8: Fix missing spaces before opening brackets/parentheses
#     text = re.sub(r'([a-z0-9])(\()', r'\1 \2', text)
#     text = re.sub(r'([a-z0-9])(\[)', r'\1 \2', text)
    
#     # Step 9: Fix missing spaces after closing brackets/parentheses
#     text = re.sub(r'(\))([A-Za-z0-9])', r'\1 \2', text)
#     text = re.sub(r'(\])([A-Za-z0-9])', r'\1 \2', text)
    
#     # Step 10: Fix multiple consecutive uppercase letters followed by lowercase
#     # "FTCand" -> "FTC and"
#     text = re.sub(r'([A-Z]{2,})([a-z])', r'\1 \2', text)
    
#     # Step 11: Replace multiple spaces with single space
#     text = re.sub(r' +', ' ', text)
    
#     # Step 12: Fix weird spacing around decimals like "2. 5" -> "2.5"
#     text = re.sub(r'(\d+)\.\s+(\d+)', r'\1.\2', text)
    
#     # Step 13: Clean up whitespace around newlines
#     text = re.sub(r'\n +', '\n', text)
#     text = re.sub(r' +\n', '\n', text)
    
#     # Step 14: Normalize multiple newlines (max 2 consecutive)
#     text = re.sub(r'\n{3,}', '\n\n', text)
    
#     # Step 15: Ensure proper spacing after list markers
#     text = re.sub(r'^(\d+\.|[-*•])\s*', r'\1 ', text, flags=re.MULTILINE)
    
#     return text.strip()


# def format_financial_numbers(text: str) -> str:
#     """
#     Additional formatting specifically for financial numbers and currencies.
    
#     Args:
#         text: Text with financial data
        
#     Returns:
#         Text with properly formatted financial numbers
#     """
#     # Ensure $ is attached to numbers (no space)
#     text = re.sub(r'\$\s+(\d)', r'$\1', text)
    
#     # Ensure space after billion/million/trillion
#     text = re.sub(r'(\d+\.?\d*)\s*billion', r'\1 billion', text, flags=re.IGNORECASE)
#     text = re.sub(r'(\d+\.?\d*)\s*million', r'\1 million', text, flags=re.IGNORECASE)
#     text = re.sub(r'(\d+\.?\d*)\s*trillion', r'\1 trillion', text, flags=re.IGNORECASE)
    
#     return text


# def format_llm_response(raw_response: str) -> str:
#     """
#     Main function to format LLM response.
#     Use this function to clean all responses before displaying.
    
#     Args:
#         raw_response: Raw text from LLM
        
#     Returns:    
#         Cleaned and formatted response ready for display
#     """
#     if not raw_response:
#         return raw_response
        
#     # Apply general text formatting
#     formatted = format_response_text(raw_response)
    
#     # Apply financial-specific formatting
#     formatted = format_financial_numbers(formatted)
    
#     return formatted