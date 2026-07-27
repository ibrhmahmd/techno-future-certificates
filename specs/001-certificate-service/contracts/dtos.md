# DTOs: Certificate Service

## Input DTOs

### GenerateCertificateInput
```python
class GenerateCertificateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    student_name: str = Field(..., min_length=1)
    course_track: str = Field(..., description="Track key (e.g., 'html', 'python')")
    level: LevelType  # Literal["Level 1 Junior", "Level 2 Intermediate", "Level 3 Advanced"]
    issue_date: date
    branch: str = Field(..., min_length=1)
    instructor: str | None = None
    director: str | None = None
    custom_color: str | None = None  # hex color
```

### RevokeCertificateInput
```python
class RevokeCertificateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    reason: str = Field(..., min_length=1)
```

## Output DTOs

### CertificateReadDTO
```python
class CertificateReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)
    
    id: int
    cert_id: str
    student_name: str
    course_name: str
    course_track: str
    level: str
    issue_date: date
    branch: str
    instructor: str | None
    director: str | None
    custom_color: str | None
    revoked_at: datetime | None
    revoked_reason: str | None
    created_at: datetime
```

### CertificateVerifyDTO
```python
class CertificateVerifyDTO(BaseModel):
    """Public verification response — excludes internal fields"""
    model_config = ConfigDict(from_attributes=True, frozen=True)
    
    cert_id: str
    student_name: str
    course_name: str
    level: str
    issue_date: date
    branch: str
    instructor: str | None
    director: str | None
    revoked: bool
    revoked_reason: str | None
```

### CertificateListResponseDTO
```python
class CertificateListResponseDTO(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    items: list[CertificateReadDTO]
    total: int
    page: int
    page_size: int
```
