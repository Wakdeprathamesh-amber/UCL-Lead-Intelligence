# 🔒 Security Notes

> **Important security considerations for this application**

## ⚠️ Current Security Status (POC)

### Authentication
- **Default credentials**: `admin` / `admin123`
- **Location**: Set via environment variables `AUTH_USERNAME` and `AUTH_PASSWORD`
- **Hashing**: SHA256 (not recommended for production - use bcrypt/argon2)
- **Session**: Stored in Streamlit session state (not persistent)

### Production Recommendations

1. **Change Default Password**
   ```bash
   export AUTH_USERNAME=your_username
   export AUTH_PASSWORD=strong_random_password
   ```

2. **Use Strong Password Hashing**
   - Replace SHA256 with bcrypt or argon2
   - Add salt to password hashing

3. **Implement Proper Session Management**
   - Use secure session tokens
   - Implement session expiration
   - Store sessions in database, not memory

4. **Add Rate Limiting**
   - Already implemented for API calls
   - Should add for login attempts

5. **Enable HTTPS**
   - Required for production deployment
   - Use reverse proxy (nginx) with SSL

6. **Audit Logging**
   - Already implemented for queries
   - Should log all authentication attempts

## 🔐 Environment Variables

Required:
- `OPENAI_API_KEY` - OpenAI API key (required)

Optional:
- `AUTH_USERNAME` - Default username (default: "admin")
- `AUTH_PASSWORD` - Default password (default: "admin123") ⚠️ **CHANGE THIS**

## 📝 Notes

- This is a POC - not production-ready for security
- Authentication is basic and should be enhanced
- No encryption at rest for database
- No role-based access control
- No multi-factor authentication

**For production deployment, implement proper authentication and authorization.**

