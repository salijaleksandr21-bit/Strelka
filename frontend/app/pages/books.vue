<template>
    <div>
        <Header>
            <h1>Источники</h1>
        </Header>
        <div v-if="loading" class="loading">Загрузка книг...</div>
        <div v-else-if="error" class="error">{{ error }}</div>

        <div v-else class="books">
            <Book
              v-for="book in books"
              :key="book.id"
              :id="book.id"
              :title="book.name"
            />
            <div class="card alt">
              <h2>Загрузить книгу</h2>
                        
              <form @submit.prevent="uploadBook" class="upload-form">
                <div class="form-group">
                  <label for="bookName">Название книги</label>
                  <input
                    id="bookName"
                    v-model="bookName"
                    type="text"
                    placeholder="Например: Война и мир"
                    required
                  />
                </div>
            
                <div class="form-group">
                  <label for="bookFile">Файл (.txt)</label>
                  <input
                    id="bookFile"
                    ref="fileInput"
                    type="file"
                    accept=".txt"
                    @change="onFileChange"
                    required
                  />
                  <small v-if="selectedFile">{{ selectedFile.name }} ({{ formatFileSize(selectedFile.size) }})</small>
                </div>
            
                <button type="submit" :disabled="uploading" class="btn-submit">
                  {{ uploading ? 'Отправка...' : 'Загрузить' }}
                </button>
            
                <div v-if="uploadError" class="error">{{ uploadError }}</div>
                <div v-if="uploadSuccess" class="success">Книга успешно добавлена!</div>
              </form>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const books = ref([])
const loading = ref(true)
const error = ref(null)

const bookName = ref('')
const selectedFile = ref(null)
const uploading = ref(false)
const uploadError = ref(null)
const uploadSuccess = ref(false)

// 📥 Загрузка списка книг при монтировании
onMounted(async () => {
  try {
    const res = await fetch('http://localhost:8000/book/library')
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail?.[0]?.msg || `HTTP ${res.status}`)
    }
    books.value = await res.json()
  } catch (e) {
    error.value = e.message
    console.error('Ошибка загрузки книг:', e)
  } finally {
    loading.value = false
  }
})

function onFileChange(event) {
  const file = event.target.files[0]
  if (file && !file.name.endsWith('.txt')) {
    alert('Пожалуйста, выберите файл с расширением .txt')
    event.target.value = ''
    return
  }
  selectedFile.value = file
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Б'
  const k = 1024
  const sizes = ['Б', 'КБ', 'МБ']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

async function uploadBook() {
  if (!bookName.value.trim()) {
    uploadError.value = 'Укажите название книги'
    return
  }
  if (!selectedFile.value) {
    uploadError.value = 'Выберите файл .txt'
    return
  }

  uploading.value = true
  uploadError.value = null
  uploadSuccess.value = false

  try {
    const formData = new FormData()
    formData.append('content', selectedFile.value)

    const url = `http://localhost:8000/book/add?name=${encodeURIComponent(bookName.value)}`
    const res = await fetch(url, {
      method: 'POST',
      body: formData,
    })

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail?.[0]?.msg || `HTTP ${res.status}`)
    }

    const data = await res.json()
    uploadSuccess.value = true

    // ✅ Обновляем список книг после успешной загрузки
    books.value.push(data)

    // Очистка формы
    bookName.value = ''
    selectedFile.value = null
    document.getElementById('bookFile')?.setAttribute('value', '')
  } catch (e) {
    uploadError.value = e.message
    console.error('Ошибка загрузки:', e)
  } finally {
    uploading.value = false
  }
}
</script>